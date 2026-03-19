import asyncio
from datetime import datetime, timezone

from celery import shared_task
from loguru import logger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.integrations.free_data_sources import FreeDataAggregator
from app.models.market_data import WatchlistSymbol
from app.schemas.market_data import MarketDataResponse
from app.services.alert_service import AlertService
from app.services.broadcast_service import BroadcastService
from app.services.market_service import MarketService


@shared_task(name="update_stock_prices")
def update_stock_prices() -> None:
    asyncio.run(_update_stock_prices())


async def _update_stock_prices() -> None:
    aggregator = FreeDataAggregator()
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(WatchlistSymbol)
                .where(WatchlistSymbol.is_active.is_(True))
                .order_by(WatchlistSymbol.priority.desc(), WatchlistSymbol.symbol.asc())
            )
            symbols = result.scalars().all()

            quotes = await aggregator.fetch_market_quotes(symbols)
            quotes_by_symbol = {quote.symbol: quote for quote in quotes}
            updated = 0
            for symbol_obj in symbols:
                quote = quotes_by_symbol.get(symbol_obj.symbol.upper())
                if quote is None:
                    await asyncio.sleep(1)
                    continue

                market_data = await MarketService.store_market_snapshot(
                    db,
                    symbol=quote.symbol,
                    name=quote.name,
                    market_type=quote.market_type,
                    exchange=quote.exchange,
                    price=quote.price,
                    open_price=quote.open_price,
                    high_price=quote.high_price,
                    low_price=quote.low_price,
                    previous_close=quote.previous_close,
                    volume=quote.volume,
                    market_cap=quote.market_cap,
                    change=quote.change,
                    change_percent=quote.change_percent,
                    currency=quote.currency,
                )
                if market_data is not None:
                    updated += 1
                    await AlertService.check_price_alerts(db, symbol_obj.symbol, market_data.price)
                    payload = MarketDataResponse.model_validate(market_data).model_dump(mode="json")
                    await BroadcastService.broadcast_market_update(symbol_obj.symbol, payload)
                await asyncio.sleep(1)

            logger.info("Updated {} stock prices", updated)
        except Exception as exc:
            logger.error("Error in stock price update task: {}", str(exc))
        finally:
            await aggregator.close()


@shared_task(name="update_currency_rates")
def update_currency_rates() -> None:
    asyncio.run(_update_currency_rates())


async def _update_currency_rates() -> None:
    aggregator = FreeDataAggregator()
    async with AsyncSessionLocal() as db:
        try:
            rates = await aggregator.fetch_currency_rates()
            indicators = await aggregator.fetch_world_bank_indicators()
            fred_indicators = await aggregator.fetch_fred_indicators()
            try:
                trading_economics = await aggregator.fetch_trading_economics_indicators()
            except Exception as exc:
                logger.warning("Trading Economics fetch failed: {}", str(exc))
                trading_economics = []

            for rate in rates:
                await MarketService.store_currency_rate_snapshot(
                    db,
                    from_currency=rate.from_currency,
                    to_currency=rate.to_currency,
                    rate=rate.rate,
                    timestamp=rate.timestamp,
                )

            for indicator in [*indicators, *fred_indicators]:
                await MarketService.store_economic_indicator(
                    db,
                    indicator_name=indicator.indicator_name,
                    indicator_code=indicator.indicator_code,
                    value=indicator.value,
                    unit=indicator.unit,
                    period=indicator.period,
                    timestamp=indicator.timestamp,
                    source=indicator.source,
                    description=indicator.description,
                    country="UAE" if indicator.source == "World Bank" else "USA",
                )

            for item in trading_economics:
                await MarketService.store_economic_indicator(
                    db,
                    indicator_name=item["category"],
                    indicator_code=item.get("ticker") or item["category"].lower().replace(" ", "_"),
                    value=item["value"],
                    unit=item.get("unit"),
                    period=item.get("date"),
                    timestamp=datetime.now(timezone.utc),
                    source="Trading Economics",
                    description=item["category"],
                    country="UAE",
                )

            logger.info(
                "Updated {} currency rates and {} economic indicators",
                len(rates),
                len(indicators) + len(fred_indicators) + len(trading_economics),
            )
        except Exception as exc:
            logger.error("Error in currency rate update task: {}", str(exc))
        finally:
            await aggregator.close()
