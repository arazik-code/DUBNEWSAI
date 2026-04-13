from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher

from app.core.circuit_breaker import CircuitBreakerOpenError, provider_health
from app.core.logging import logger
from app.core.providers import ProviderConfig, ProviderType, provider_registry
from app.integrations.free_data_sources import FreeDataAggregator, NormalizedNewsRecord
from app.schemas.news import NewsArticleCreate


@dataclass(slots=True)
class AggregatedNewsItem:
    article: NewsArticleCreate
    url_hash: str
    source_providers: list[str]
    duplicate_count: int
    quality_score: float


@dataclass(slots=True)
class NewsAggregationResult:
    items: list[AggregatedNewsItem]
    total_raw: int
    total_unique: int
    provider_stats: dict[str, dict[str, object]]
    query: str
    timestamp: str


class NewsAggregator:
    DEFAULT_QUERY = "Dubai real estate"
    QUERY_THEMES: tuple[str, ...] = (
        "Dubai property market",
        "UAE real estate investment",
        "Dubai rents and yields",
        "Emaar OR Aldar OR Damac OR Deyaar",
        "Abu Dhabi property market",
        "Dubai off-plan launches",
        "Dubai mortgage rates",
        "Dubai property regulation OR RERA OR DLD",
    )
    PROVIDER_POLL_MINUTES: dict[str, int] = {
        "rss_feeds": 2,
        "web_scrapers": 5,
        "currents": 5,
        "thenewsapi": 10,
        "newsapi_ai": 10,
        "newsdata": 10,
        "gnews": 20,
        "newsapi": 20,
        "mediastack": 30,
        "contextual_web": 30,
        "bing_news": 180,
    }
    PROVIDER_QUERY_BUDGET: dict[str, int] = {
        "newsapi": 3,
        "gnews": 2,
        "currents": 2,
        "thenewsapi": 2,
        "newsdata": 2,
        "newsapi_ai": 2,
        "mediastack": 1,
        "contextual_web": 1,
        "bing_news": 1,
        "rss_feeds": 1,
        "web_scrapers": 1,
    }

    def __init__(self) -> None:
        self.registry = provider_registry

    async def aggregate_news(
        self,
        *,
        query: str | None = None,
        max_articles: int = 100,
        include_rss: bool = True,
        include_scraped: bool = True,
    ) -> NewsAggregationResult:
        effective_query = query or self.DEFAULT_QUERY
        provider_stats: dict[str, dict[str, object]] = {}
        raw_records: list[NormalizedNewsRecord] = []
        now = datetime.now(timezone.utc)

        aggregator = FreeDataAggregator()
        try:
            providers = [
                provider
                for provider in self.registry.get_healthy_providers(ProviderType.NEWS, min_reliability=55.0)
                if (include_rss or provider.name != "rss_feeds")
                and (include_scraped or provider.name != "web_scrapers")
            ]

            scheduled_providers: list[ProviderConfig] = []
            scheduled_queries: list[list[str]] = []
            tasks: list[object] = []
            for provider in providers:
                if not self._should_poll_provider(provider.name, now):
                    provider_stats[provider.name] = self._provider_skipped_stats(provider.name)
                    continue
                queries = self._queries_for_provider(provider.name, effective_query, now)
                scheduled_providers.append(provider)
                scheduled_queries.append(queries)
                tasks.append(self._fetch_from_provider(aggregator, provider, queries))

            results = await self._gather(tasks)

            for provider, queries, result in zip(scheduled_providers, scheduled_queries, results):
                if isinstance(result, Exception):
                    provider_stats[provider.name] = self._provider_error_stats(provider.name, result, queries=queries)
                    continue
                raw_records.extend(result)
                provider_stats[provider.name] = self._provider_success_stats(provider.name, len(result), queries=queries)

            deduped = self._deduplicate_articles(raw_records)
            ranked = sorted(
                deduped,
                key=lambda item: (item.quality_score, item.article.published_at),
                reverse=True,
            )

            return NewsAggregationResult(
                items=ranked[:max_articles],
                total_raw=len(raw_records),
                total_unique=len(deduped),
                provider_stats=provider_stats,
                query=effective_query,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        finally:
            await aggregator.close()

    @classmethod
    def _should_poll_provider(cls, provider_name: str, now: datetime) -> bool:
        cadence_minutes = cls.PROVIDER_POLL_MINUTES.get(provider_name, 15)
        if cadence_minutes <= 1:
            return True
        minute_of_day = now.hour * 60 + now.minute
        return minute_of_day % cadence_minutes == 0

    async def _gather(self, tasks: list[object]) -> list[object]:
        import asyncio

        return list(await asyncio.gather(*tasks, return_exceptions=True))

    async def _fetch_from_provider(
        self,
        aggregator: FreeDataAggregator,
        provider: ProviderConfig,
        queries: list[str],
    ) -> list[NormalizedNewsRecord]:
        fetcher = {
            "rss_feeds": aggregator._fetch_rss,
            "web_scrapers": aggregator._fetch_scraped_news,
        }.get(provider.name)
        if fetcher is None:
            fetcher = lambda: []

        if provider.name in {"rss_feeds", "web_scrapers"}:
            try:
                return await provider_health.call_provider(provider.name, fetcher)
            except CircuitBreakerOpenError:
                logger.warning("News provider {} skipped because its circuit breaker is open", provider.name)
                raise

        records: list[NormalizedNewsRecord] = []
        seen_urls: set[str] = set()
        for query in queries:
            fetcher = {
                "newsapi": lambda query=query: aggregator._fetch_newsapi(query=query),
                "gnews": lambda query=query: aggregator._fetch_gnews(query=query),
                "currents": lambda query=query: aggregator._fetch_currents(query=query),
                "newsdata": lambda query=query: aggregator._fetch_newsdata(query=query),
                "thenewsapi": lambda query=query: aggregator._fetch_thenewsapi(query=query),
                "mediastack": lambda query=query: aggregator._fetch_mediastack(query=query),
                "newsapi_ai": lambda query=query: aggregator._fetch_newsapi_ai(query=query),
                "bing_news": lambda query=query: aggregator._fetch_bing_news(query=query),
                "contextual_web": lambda query=query: aggregator._fetch_contextual_web(query=query),
            }.get(provider.name)
            if fetcher is None:
                continue
            try:
                fetched_records = await provider_health.call_provider(provider.name, fetcher)
            except CircuitBreakerOpenError:
                logger.warning("News provider {} skipped because its circuit breaker is open", provider.name)
                raise
            for record in fetched_records:
                if record.url in seen_urls:
                    continue
                seen_urls.add(record.url)
                records.append(record)
        return records

    @staticmethod
    def _provider_success_stats(provider_name: str, count: int, *, queries: list[str] | None = None) -> dict[str, object]:
        state = provider_health.snapshot(provider_name)
        return {
            "status": "success",
            "count": count,
            "state": state.state,
            "reliability": state.reliability,
            "last_error": state.last_error,
            "queries": queries or [],
        }

    @staticmethod
    def _provider_error_stats(provider_name: str, error: Exception, *, queries: list[str] | None = None) -> dict[str, object]:
        state = provider_health.snapshot(provider_name)
        return {
            "status": "failed",
            "count": 0,
            "state": state.state,
            "reliability": state.reliability,
            "last_error": str(error),
            "queries": queries or [],
        }

    @staticmethod
    def _provider_skipped_stats(provider_name: str) -> dict[str, object]:
        state = provider_health.snapshot(provider_name)
        return {
            "status": "skipped",
            "count": 0,
            "state": state.state,
            "reliability": state.reliability,
            "last_error": None,
        }

    def _queries_for_provider(self, provider_name: str, query: str, now: datetime) -> list[str]:
        if provider_name in {"rss_feeds", "web_scrapers"}:
            return [query]

        budget = max(1, self.PROVIDER_QUERY_BUDGET.get(provider_name, 1))
        rotated_themes = list(self.QUERY_THEMES)
        if rotated_themes:
            offset = (now.hour + sum(ord(char) for char in provider_name)) % len(rotated_themes)
            rotated_themes = rotated_themes[offset:] + rotated_themes[:offset]

        queries = [query]
        for theme in rotated_themes:
            if len(queries) >= budget:
                break
            if theme.lower() == query.lower():
                continue
            queries.append(theme)
        return list(dict.fromkeys(item.strip() for item in queries if item.strip()))

    @staticmethod
    def _normalize_title(title: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() else " " for char in title)
        return " ".join(normalized.split())

    def _provider_for_record(self, provider_name: str) -> ProviderConfig | None:
        provider = self.registry.get_provider(provider_name)
        if provider is not None:
            return provider
        if provider_name.startswith("rss_"):
            return self.registry.get_provider("rss_feeds")
        if provider_name.startswith("scraper_"):
            return self.registry.get_provider("web_scrapers")
        return None

    def _are_duplicates(self, left: NormalizedNewsRecord, right: NormalizedNewsRecord) -> bool:
        if left.url == right.url:
            return True
        left_title = self._normalize_title(left.title)
        right_title = self._normalize_title(right.title)
        if not left_title or not right_title:
            return False
        if left_title == right_title:
            return True
        similarity = SequenceMatcher(a=left_title, b=right_title).ratio()
        published_gap = abs((left.published_at - right.published_at).total_seconds())
        return similarity >= 0.92 and published_gap <= 36 * 3600

    @staticmethod
    def _content_length(record: NormalizedNewsRecord) -> int:
        return len((record.content or "").strip()) + len((record.description or "").strip())

    def _pick_preferred(self, left: NormalizedNewsRecord, right: NormalizedNewsRecord) -> NormalizedNewsRecord:
        left_provider = self._provider_for_record(left.source_provider)
        right_provider = self._provider_for_record(right.source_provider)
        left_reliability = left_provider.reliability_score if left_provider else 50.0
        right_reliability = right_provider.reliability_score if right_provider else 50.0

        left_score = left_reliability + self._content_length(left) * 0.001 + (5 if left.image_url else 0)
        right_score = right_reliability + self._content_length(right) * 0.001 + (5 if right.image_url else 0)
        return left if left_score >= right_score else right

    def _score_record(
        self,
        record: NormalizedNewsRecord,
        *,
        duplicate_count: int,
        provider_names: list[str],
    ) -> float:
        provider = self._provider_for_record(record.source_provider)
        provider_score = provider.reliability_score if provider else 55.0

        age_hours = max(
            0.0,
            (datetime.now(timezone.utc) - record.published_at.astimezone(timezone.utc)).total_seconds() / 3600,
        )
        recency_bonus = max(0.0, 24.0 - min(age_hours, 24.0))
        completeness_bonus = 0.0
        if record.description:
            completeness_bonus += 6.0
        if record.content:
            completeness_bonus += min(16.0, len(record.content) / 900)
        if record.image_url:
            completeness_bonus += 4.0

        keyword_bonus = 0.0
        lowered = f"{record.title} {record.description or ''}".lower()
        for keyword in ("dubai", "uae", "property", "real estate", "rental", "emaar", "damac", "aldar", "deyaar"):
            if keyword in lowered:
                keyword_bonus += 2.0

        cross_source_bonus = min(18.0, (duplicate_count - 1) * 4.0 + max(0, len(set(provider_names)) - 1) * 2.0)
        return min(100.0, provider_score * 0.45 + recency_bonus + completeness_bonus + keyword_bonus + cross_source_bonus)

    def _deduplicate_articles(self, records: list[NormalizedNewsRecord]) -> list[AggregatedNewsItem]:
        groups: list[dict[str, object]] = []

        for record in sorted(records, key=lambda item: item.published_at, reverse=True):
            matching_group: dict[str, object] | None = None
            for group in groups:
                if self._are_duplicates(group["primary"], record):  # type: ignore[index]
                    matching_group = group
                    break

            if matching_group is None:
                groups.append(
                    {
                        "primary": record,
                        "providers": [record.source_provider],
                        "duplicates": 1,
                    }
                )
                continue

            current_primary = matching_group["primary"]  # type: ignore[index]
            preferred = self._pick_preferred(current_primary, record)
            matching_group["primary"] = preferred
            matching_group["duplicates"] = int(matching_group["duplicates"]) + 1  # type: ignore[index]
            providers = matching_group["providers"]  # type: ignore[index]
            if record.source_provider not in providers:
                providers.append(record.source_provider)

        aggregated_items: list[AggregatedNewsItem] = []
        for group in groups:
            primary = group["primary"]  # type: ignore[assignment]
            providers = group["providers"]  # type: ignore[assignment]
            duplicate_count = int(group["duplicates"])  # type: ignore[arg-type]
            quality_score = self._score_record(primary, duplicate_count=duplicate_count, provider_names=providers)
            article = NewsArticleCreate(
                title=primary.title,
                description=primary.description,
                content=primary.content,
                url=primary.url,
                source=primary.source,
                source_name=primary.source_name,
                author=primary.author,
                category=primary.category,
                published_at=primary.published_at,
                image_url=primary.image_url,
            )
            aggregated_items.append(
                AggregatedNewsItem(
                    article=article,
                    url_hash=hashlib.sha256(primary.url.encode("utf-8")).hexdigest(),
                    source_providers=list(dict.fromkeys(providers)),
                    duplicate_count=duplicate_count,
                    quality_score=quality_score,
                )
            )
        return aggregated_items


news_aggregator = NewsAggregator()
