from __future__ import annotations

import asyncio

from celery import shared_task
from loguru import logger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.market_data import WatchlistSymbol
from app.schemas.market_data import MarketDataResponse
from app.schemas.news import NewsArticleResponse
from app.services.alert_service import AlertService
from app.services.aggregation.market_aggregator import market_aggregator
from app.services.aggregation.news_aggregator import news_aggregator
from app.services.broadcast_service import BroadcastService
from app.services.market_service import MarketService
from app.services.news_service import NewsService


@shared_task(name="aggregate_all_news_sources")
def aggregate_all_news_sources() -> None:
    asyncio.run(_aggregate_all_news_sources())


@shared_task(name="aggregate_full_market_data")
def aggregate_full_market_data() -> None:
    asyncio.run(_aggregate_full_market_data())


async def _aggregate_all_news_sources() -> dict[str, object]:
    result = await news_aggregator.aggregate_news()

    async with AsyncSessionLocal() as db:
        created_ranked: list[tuple[float, object]] = []
        skipped = 0

        for item in result.items:
            created_article = await NewsService.create_article(db, item.article)
            if created_article is None:
                skipped += 1
                continue
            created_ranked.append((item.quality_score, created_article))

        for _, article in sorted(created_ranked, key=lambda pair: pair[0], reverse=True)[:5]:
            try:
                await NewsService.enrich_article_content(db, article)
            except Exception as exc:
                logger.debug("Article enrichment skipped for {}: {}", article.url, str(exc))

        for _, article in created_ranked:
            await AlertService.check_keyword_alerts(db, article)
            await AlertService.check_sentiment_alerts(db, article)
            await AlertService.check_category_alerts(db, article)
            payload = NewsArticleResponse.model_validate(article).model_dump(mode="json")
            await BroadcastService.broadcast_new_article(payload)

    summary = {
        "created": len(created_ranked),
        "skipped": skipped,
        "total_raw": result.total_raw,
        "total_unique": result.total_unique,
        "provider_stats": result.provider_stats,
    }
    logger.info(
        "Enterprise news aggregation complete: {} created, {} skipped, {} raw, {} unique",
        summary["created"],
        summary["skipped"],
        summary["total_raw"],
        summary["total_unique"],
    )
    return summary


async def _aggregate_full_market_data() -> dict[str, object]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WatchlistSymbol)
            .where(WatchlistSymbol.is_active.is_(True))
            .order_by(WatchlistSymbol.priority.desc(), WatchlistSymbol.symbol.asc())
        )
        watchlist_symbols = result.scalars().all()

        market_result = await market_aggregator.aggregate_full_market_data(watchlist_symbols=watchlist_symbols)

        saved_quotes = 0
        for collection_name in ("uae_stocks", "global_real_estate", "indices", "commodities"):
            for quote in market_result[collection_name]:
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
                saved_quotes += 1
                await AlertService.check_price_alerts(db, quote.symbol, quote.price)
                payload = MarketDataResponse.model_validate(market_data).model_dump(mode="json")
                await BroadcastService.broadcast_market_update(quote.symbol, payload)

        for rate in market_result["currencies"]:
            await MarketService.store_currency_rate_snapshot(
                db,
                from_currency=rate.from_currency,
                to_currency=rate.to_currency,
                rate=rate.rate,
                timestamp=rate.timestamp,
            )

        for indicator in market_result["economic_indicators"]:
            country = "USA" if indicator.source.startswith("FRED") else "UAE"
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
                country=country,
            )

    summary = {
        "saved_quotes": saved_quotes,
        "currencies": len(market_result["currencies"]),
        "economic_indicators": len(market_result["economic_indicators"]),
        "provider_stats": market_result["provider_stats"],
    }
    logger.info(
        "Enterprise market aggregation complete: {} quotes, {} FX pairs, {} indicators",
        summary["saved_quotes"],
        summary["currencies"],
        summary["economic_indicators"],
    )
    return summary
