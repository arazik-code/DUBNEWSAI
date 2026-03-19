from app.core.logging import logger
from app.tasks.aggregation_tasks import _aggregate_all_news_sources, _aggregate_full_market_data


class AggregatorService:
    async def run_ingestion_cycle(self) -> dict[str, str]:
        logger.info("Aggregator ingestion cycle requested")
        await _aggregate_all_news_sources()
        await _aggregate_full_market_data()
        return {"status": "completed"}
