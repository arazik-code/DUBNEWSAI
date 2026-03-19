import asyncio
from contextlib import suppress

from loguru import logger
from sqlalchemy import func, select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.market_data import MarketData
from app.models.news import NewsArticle
from app.tasks.market_tasks import _update_currency_rates, _update_stock_prices
from app.tasks.news_tasks import _fetch_newsapi_articles, _fetch_rss_feeds

settings = get_settings()


class EmbeddedSyncService:
    @staticmethod
    async def _published_article_count() -> int:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count()).select_from(NewsArticle).where(NewsArticle.is_published.is_(True))
            )
            return int(result.scalar_one() or 0)

    @staticmethod
    async def bootstrap_news_if_empty() -> None:
        article_count = await EmbeddedSyncService._published_article_count()
        if article_count > 0:
            logger.info("Skipping news bootstrap; {} published articles already exist", article_count)
            return

        logger.info("Bootstrapping news feed for single-service production deployment")
        await EmbeddedSyncService.run_news_sync()

    @staticmethod
    async def _market_snapshot_count() -> int:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(func.count()).select_from(MarketData))
            return int(result.scalar_one() or 0)

    @staticmethod
    async def bootstrap_market_if_empty() -> None:
        market_count = await EmbeddedSyncService._market_snapshot_count()
        if market_count > 0:
            logger.info("Skipping market bootstrap; {} market snapshots already exist", market_count)
            return

        logger.info("Bootstrapping market feeds for single-service production deployment")
        await EmbeddedSyncService.run_market_sync()

    @staticmethod
    async def run_news_sync() -> None:
        try:
            await _fetch_newsapi_articles()
        except Exception as exc:
            logger.error("Embedded NewsAPI sync failed: {}", str(exc))

        try:
            await _fetch_rss_feeds()
        except Exception as exc:
            logger.error("Embedded RSS sync failed: {}", str(exc))

    @staticmethod
    async def run_news_sync_loop() -> None:
        interval_seconds = max(5, settings.EMBEDDED_NEWS_SYNC_MINUTES) * 60
        logger.info(
            "Embedded news sync loop enabled; running every {} minute(s)",
            max(5, settings.EMBEDDED_NEWS_SYNC_MINUTES),
        )

        while True:
            try:
                await EmbeddedSyncService.run_news_sync()
            except Exception as exc:
                logger.error("Embedded news sync loop iteration failed: {}", str(exc))

            await asyncio.sleep(interval_seconds)

    @staticmethod
    async def run_market_sync() -> None:
        try:
            await _update_stock_prices()
        except Exception as exc:
            logger.error("Embedded stock sync failed: {}", str(exc))

        try:
            await _update_currency_rates()
        except Exception as exc:
            logger.error("Embedded currency sync failed: {}", str(exc))

    @staticmethod
    async def run_market_sync_loop() -> None:
        interval_seconds = max(15, settings.EMBEDDED_MARKET_SYNC_MINUTES) * 60
        logger.info(
            "Embedded market sync loop enabled; running every {} minute(s)",
            max(15, settings.EMBEDDED_MARKET_SYNC_MINUTES),
        )

        while True:
            try:
                await EmbeddedSyncService.run_market_sync()
            except Exception as exc:
                logger.error("Embedded market sync loop iteration failed: {}", str(exc))

            await asyncio.sleep(interval_seconds)

    @staticmethod
    async def shutdown_task(task: asyncio.Task[None] | None) -> None:
        if task is None:
            return

        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
