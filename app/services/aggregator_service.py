from app.core.logging import logger
from app.tasks.market_tasks import _update_currency_rates, _update_stock_prices
from app.tasks.news_tasks import _fetch_newsapi_articles, _fetch_rss_feeds


class AggregatorService:
    async def run_ingestion_cycle(self) -> dict[str, str]:
        logger.info("Aggregator ingestion cycle requested")
        await _fetch_newsapi_articles()
        await _fetch_rss_feeds()
        await _update_stock_prices()
        await _update_currency_rates()
        return {"status": "completed"}
