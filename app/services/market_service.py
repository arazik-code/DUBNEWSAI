from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.metrics import market_updates
from app.integrations.alpha_vantage_client import AlphaVantageClient
from app.schemas.market_data import MarketDataResponse
from app.models.market_data import CurrencyRate, MarketData, MarketType, WatchlistSymbol


class MarketService:
    @staticmethod
    def _watchlist_to_market_snapshot(watchlist: WatchlistSymbol) -> dict:
        return {
            "id": watchlist.id,
            "symbol": watchlist.symbol,
            "name": watchlist.name,
            "market_type": watchlist.market_type,
            "exchange": watchlist.exchange,
            "price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "volume": 0,
            "market_cap": None,
            "data_timestamp": datetime.now(timezone.utc),
            "is_live_data": False,
            "data_source": "watchlist_fallback",
        }

    @staticmethod
    async def _get_watchlist_fallback(
        db: AsyncSession,
        market_type: MarketType | None = None,
        limit: int = 50,
        real_estate_only: bool = False,
    ) -> list[dict]:
        query = (
            select(WatchlistSymbol)
            .where(WatchlistSymbol.is_active.is_(True))
            .order_by(WatchlistSymbol.priority.desc(), WatchlistSymbol.symbol.asc())
        )
        if market_type is not None:
            query = query.where(WatchlistSymbol.market_type == market_type)
        if real_estate_only:
            query = query.where(WatchlistSymbol.is_real_estate_company.is_(True))

        result = await db.execute(query.limit(limit))
        return [MarketService._watchlist_to_market_snapshot(item) for item in result.scalars().all()]

    @staticmethod
    async def update_stock_quote(
        db: AsyncSession,
        symbol: str,
        client: AlphaVantageClient,
    ) -> MarketData | None:
        try:
            quote_data = await client.get_quote(symbol)
            if not quote_data:
                return None

            watchlist_result = await db.execute(
                select(WatchlistSymbol).where(WatchlistSymbol.symbol == symbol.upper())
            )
            watchlist = watchlist_result.scalar_one_or_none()
            if watchlist is None:
                logger.warning("Symbol {} not found in watchlist", symbol)
                return None

            market_data = MarketData(
                symbol=watchlist.symbol,
                name=watchlist.name,
                market_type=watchlist.market_type,
                exchange=watchlist.exchange,
                price=float(quote_data.get("05. price", 0) or 0),
                open_price=float(quote_data.get("02. open", 0) or 0),
                high_price=float(quote_data.get("03. high", 0) or 0),
                low_price=float(quote_data.get("04. low", 0) or 0),
                close_price=float(quote_data.get("08. previous close", 0) or 0),
                previous_close=float(quote_data.get("08. previous close", 0) or 0),
                volume=int(float(quote_data.get("06. volume", 0) or 0)),
                market_cap=None,
                change=float(quote_data.get("09. change", 0) or 0),
                change_percent=float(str(quote_data.get("10. change percent", "0")).replace("%", "") or 0),
                data_timestamp=datetime.now(timezone.utc),
            )
            db.add(market_data)
            await db.commit()
            await db.refresh(market_data)
            await cache.delete_pattern("market_latest:*")
            await cache.delete(cache.MARKET_SYMBOL.format(symbol=symbol.upper()))
            await cache.delete(cache.MARKET_REAL_ESTATE)
            await cache.delete(cache.MARKET_OVERVIEW)
            market_updates.inc()
            logger.info("Updated market quote for {}", symbol)
            return market_data
        except Exception as exc:
            logger.error("Error updating market quote for {}: {}", symbol, str(exc))
            return None

    @staticmethod
    async def update_currency_rate(
        db: AsyncSession,
        from_currency: str,
        to_currency: str,
        client: AlphaVantageClient,
    ) -> CurrencyRate | None:
        try:
            rate_data = await client.get_currency_exchange_rate(from_currency, to_currency)
            if not rate_data:
                return None

            currency_rate = CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=float(rate_data.get("5. Exchange Rate", 0) or 0),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(currency_rate)
            await db.commit()
            await db.refresh(currency_rate)
            logger.info("Updated currency rate {}/{}", from_currency, to_currency)
            return currency_rate
        except Exception as exc:
            logger.error("Error updating currency rate {}/{}: {}", from_currency, to_currency, str(exc))
            return None

    @staticmethod
    async def get_latest_market_data(
        db: AsyncSession,
        market_type: MarketType | None = None,
        limit: int = 50,
    ) -> list[MarketData] | list[dict]:
        cache_suffix = market_type.value if market_type is not None else "all"
        cache_key = f"market_latest:{cache_suffix}:{limit}"
        cached_market = await cache.get(cache_key)
        if cached_market is not None:
            return cached_market

        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .group_by(MarketData.symbol)
            .subquery()
        )

        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        )

        if market_type is not None:
            query = query.where(MarketData.market_type == market_type)

        query = query.order_by(desc(MarketData.data_timestamp)).limit(limit)
        result = await db.execute(query)
        rows = list(result.scalars().all())
        if not rows:
            fallback_rows = await MarketService._get_watchlist_fallback(db, market_type=market_type, limit=limit)
            if fallback_rows:
                await cache.set(cache_key, fallback_rows, ttl=60)
                return fallback_rows
        serialized = [MarketDataResponse.model_validate(row).model_dump(mode="json") for row in rows]
        await cache.set(cache_key, serialized, ttl=60)
        return serialized

    @staticmethod
    async def get_real_estate_companies(db: AsyncSession) -> list[MarketData] | list[dict]:
        cached_companies = await cache.get_cached_market_real_estate()
        if cached_companies is not None:
            return [MarketDataResponse.model_validate(company) for company in cached_companies]

        watchlist_result = await db.execute(
            select(WatchlistSymbol).where(
                WatchlistSymbol.is_real_estate_company.is_(True),
                WatchlistSymbol.is_active.is_(True),
            )
        )
        watchlist_symbols = watchlist_result.scalars().all()
        if not watchlist_symbols:
            return []

        symbols = [symbol.symbol for symbol in watchlist_symbols]
        subquery = (
            select(
                MarketData.symbol,
                func.max(MarketData.data_timestamp).label("max_timestamp"),
            )
            .where(MarketData.symbol.in_(symbols))
            .group_by(MarketData.symbol)
            .subquery()
        )
        query = select(MarketData).join(
            subquery,
            and_(
                MarketData.symbol == subquery.c.symbol,
                MarketData.data_timestamp == subquery.c.max_timestamp,
            ),
        ).order_by(MarketData.symbol.asc())
        result = await db.execute(query)
        companies = list(result.scalars().all())
        if not companies:
            fallback_companies = await MarketService._get_watchlist_fallback(
                db,
                market_type=MarketType.STOCK,
                real_estate_only=True,
            )
            await cache.cache_market_real_estate(fallback_companies, ttl=120)
            return [MarketDataResponse.model_validate(company) for company in fallback_companies]
        await cache.cache_market_real_estate(
            [MarketDataResponse.model_validate(company).model_dump(mode="json") for company in companies],
            ttl=120,
        )
        return companies

    @staticmethod
    async def get_latest_currency_rates(db: AsyncSession, limit: int = 10) -> list[CurrencyRate]:
        subquery = (
            select(
                CurrencyRate.from_currency,
                CurrencyRate.to_currency,
                func.max(CurrencyRate.timestamp).label("max_timestamp"),
            )
            .group_by(CurrencyRate.from_currency, CurrencyRate.to_currency)
            .subquery()
        )
        query = (
            select(CurrencyRate)
            .join(
                subquery,
                and_(
                    CurrencyRate.from_currency == subquery.c.from_currency,
                    CurrencyRate.to_currency == subquery.c.to_currency,
                    CurrencyRate.timestamp == subquery.c.max_timestamp,
                ),
            )
            .order_by(desc(CurrencyRate.timestamp))
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_symbol_data(db: AsyncSession, symbol: str) -> MarketData | dict | None:
        cached_symbol = await cache.get_cached_market_symbol(symbol)
        if cached_symbol is not None:
            return cached_symbol

        result = await db.execute(
            select(MarketData)
            .where(MarketData.symbol == symbol.upper())
            .order_by(MarketData.data_timestamp.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest is not None:
            await cache.cache_market_symbol(
                symbol,
                MarketDataResponse.model_validate(latest).model_dump(mode="json"),
                ttl=60,
            )
            return latest

        watchlist_result = await db.execute(
            select(WatchlistSymbol)
            .where(WatchlistSymbol.symbol == symbol.upper(), WatchlistSymbol.is_active.is_(True))
            .limit(1)
        )
        watchlist = watchlist_result.scalar_one_or_none()
        if watchlist is None:
            return None

        fallback_snapshot = MarketService._watchlist_to_market_snapshot(watchlist)
        await cache.cache_market_symbol(symbol, fallback_snapshot, ttl=60)
        return fallback_snapshot
