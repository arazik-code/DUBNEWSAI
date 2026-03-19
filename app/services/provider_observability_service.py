from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit_breaker import provider_health
from app.core.providers import ProviderPriority, ProviderType, provider_registry
from app.models.market_data import MarketData
from app.models.news import NewsArticle
from app.models.sources import ArticleSource, DataProvider, MarketDataSource, ProviderFetchLog


class ProviderObservabilityService:
    @staticmethod
    async def sync_registry_to_db(db: AsyncSession) -> dict[str, DataProvider]:
        result = await db.execute(select(DataProvider))
        existing = {provider.name: provider for provider in result.scalars().all()}

        synced: dict[str, DataProvider] = {}
        for config in provider_registry.providers.values():
            provider = existing.get(config.name)
            if provider is None:
                provider = DataProvider(name=config.name, type=config.type.value)
                db.add(provider)

            provider.type = config.type.value
            provider.priority = int(config.priority.value if isinstance(config.priority, ProviderPriority) else config.priority)
            provider.rate_limit_per_day = config.rate_limit
            provider.cost_per_call = config.cost_per_call
            provider.is_enabled = config.enabled
            provider.base_url = config.base_url or None
            provider.timeout_seconds = config.timeout
            provider.retry_attempts = config.retry_attempts
            provider.provider_metadata = dict(config.metadata)

            state = provider_health.snapshot(config.name)
            provider.is_healthy = state.state != "open"
            provider.reliability_score = state.reliability if state.successes or state.failures else config.reliability_score
            provider.total_calls = state.successes + state.failures
            provider.successful_calls = state.successes
            provider.failed_calls = state.failures
            provider.last_success_at = state.last_success_at
            provider.last_failure_at = state.last_failure_at
            provider.circuit_state = state.state
            provider.circuit_opened_at = state.opened_at
            provider.failure_count = state.consecutive_failures

            synced[config.name] = provider

        await db.flush()
        return synced

    @staticmethod
    async def record_provider_stats(
        db: AsyncSession,
        provider_stats: dict[str, dict[str, object]],
        *,
        query: str | None = None,
        fetch_type: str,
        triggered_by: str,
        task_id: str | None = None,
    ) -> dict[str, DataProvider]:
        providers = await ProviderObservabilityService.sync_registry_to_db(db)

        for provider_name, stats in provider_stats.items():
            provider = providers.get(provider_name)
            if provider is None:
                provider_type = ProviderType.NEWS.value if fetch_type == "news_aggregation" else ProviderType.MARKET.value
                provider = DataProvider(name=provider_name, type=provider_type)
                db.add(provider)
                await db.flush()
                providers[provider_name] = provider

            status = str(stats.get("status", "success"))
            count = int(stats.get("count", 0) or 0)
            last_error = stats.get("last_error")
            db.add(
                ProviderFetchLog(
                    provider_id=provider.id,
                    query=query,
                    fetch_type=fetch_type,
                    status=status,
                    items_fetched=count,
                    response_time_ms=None,
                    error_message=str(last_error) if last_error else None,
                    error_type=type(last_error).__name__ if isinstance(last_error, Exception) else None,
                    triggered_by=triggered_by,
                    task_id=task_id,
                )
            )

        await db.flush()
        return providers

    @staticmethod
    async def attach_article_sources(
        db: AsyncSession,
        *,
        article: NewsArticle,
        provider_names: list[str],
        primary_provider: str | None,
        duplicate_count: int,
        quality_score: float,
    ) -> None:
        providers = await ProviderObservabilityService.sync_registry_to_db(db)
        existing_result = await db.execute(select(ArticleSource).where(ArticleSource.article_id == article.id))
        providers_by_id = {provider.id: provider for provider in providers.values() if provider.id is not None}
        existing_by_provider = {
            providers_by_id[item.provider_id].name: item
            for item in existing_result.scalars().all()
            if item.provider_id in providers_by_id
        }

        article.primary_provider = primary_provider
        article.duplicate_count = duplicate_count
        article.quality_score = quality_score

        ordered_provider_names = list(dict.fromkeys(provider_names))
        for provider_name in ordered_provider_names:
            provider = providers.get(provider_name)
            if provider is None:
                continue

            source_row = existing_by_provider.get(provider_name)
            if source_row is None:
                source_row = ArticleSource(
                    article_id=article.id,
                    provider_id=provider.id,
                )
                db.add(source_row)

            source_row.source_url = article.url
            source_row.source_title = article.title
            source_row.source_description = article.description
            source_row.source_quality_score = quality_score
            source_row.is_primary = provider_name == primary_provider

        await db.flush()

    @staticmethod
    async def attach_market_sources(
        db: AsyncSession,
        *,
        market_data: MarketData,
        provider_names: list[str],
        primary_provider: str | None,
        confidence_score: float | None = None,
        data_completeness: float | None = None,
    ) -> None:
        providers = await ProviderObservabilityService.sync_registry_to_db(db)
        existing_result = await db.execute(select(MarketDataSource).where(MarketDataSource.market_data_id == market_data.id))
        providers_by_id = {provider.id: provider for provider in providers.values() if provider.id is not None}
        existing_by_provider = {
            providers_by_id[item.provider_id].name: item
            for item in existing_result.scalars().all()
            if item.provider_id in providers_by_id
        }

        market_data.primary_provider = primary_provider
        market_data.data_quality_score = data_completeness
        market_data.confidence_level = (
            "high" if (confidence_score or 0) >= 80 else "medium" if (confidence_score or 0) >= 50 else "low"
        ) if confidence_score is not None else None

        for provider_name in list(dict.fromkeys(provider_names)):
            provider = providers.get(provider_name)
            if provider is None:
                continue

            source_row = existing_by_provider.get(provider_name)
            if source_row is None:
                source_row = MarketDataSource(
                    market_data_id=market_data.id,
                    provider_id=provider.id,
                )
                db.add(source_row)

            source_row.data_completeness = data_completeness
            source_row.confidence_score = confidence_score

        await db.flush()
