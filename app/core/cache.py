from __future__ import annotations

import hashlib
import json
from functools import wraps
from typing import Any

import redis.asyncio as redis
from loguru import logger
from pydantic import BaseModel

from app.config import get_settings
from app.schemas.news import NewsFilterParams

settings = get_settings()


class CacheService:
    """Redis-backed caching helper with graceful fallback."""

    NEWS_LIST = "news:list:{filters_hash}"
    NEWS_DETAIL = "news:detail:{article_id}"
    NEWS_TRENDING = "news:trending:{timeframe}"
    NEWS_FEATURED = "news:featured"

    MARKET_OVERVIEW = "market:overview"
    MARKET_SYMBOL = "market:symbol:{symbol}"
    MARKET_REAL_ESTATE = "market:real_estate"
    MARKET_WEATHER = "market:weather"

    ANALYTICS_TRENDS = "analytics:trends:{days}"
    ANALYTICS_SENTIMENT = "analytics:sentiment:{category}:{days}"

    USER_PREFERENCES = "user:prefs:{user_id}"
    USER_ALERTS = "user:alerts:{user_id}"

    def __init__(self) -> None:
        self.redis_client: redis.Redis | None = None
        self._connected = False

    async def connect(self) -> None:
        if self._connected:
            return

        try:
            client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await client.ping()
            self.redis_client = client
            self._connected = True
            logger.info("Cache service connected to Redis")
        except Exception as exc:
            self.redis_client = None
            self._connected = False
            logger.warning("Cache service unavailable: {}", str(exc))

    async def disconnect(self) -> None:
        if self.redis_client is None:
            self._connected = False
            return

        close_method = getattr(self.redis_client, "aclose", None)
        if close_method is not None:
            await close_method()
        else:  # pragma: no cover - compatibility path
            await self.redis_client.close()

        self.redis_client = None
        self._connected = False
        logger.info("Cache service disconnected")

    async def get(self, key: str) -> Any | None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return None

        try:
            value = await self.redis_client.get(key)
            if value is None:
                self._track_cache_miss()
                return None

            self._track_cache_hit()
            return json.loads(value)
        except Exception as exc:
            logger.error("Cache get error for {}: {}", key, str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return

        try:
            await self.redis_client.setex(key, ttl, json.dumps(self._serialize(value), default=str))
            logger.debug("Cached {} with ttl={}s", key, ttl)
        except Exception as exc:
            logger.error("Cache set error for {}: {}", key, str(exc))

    async def delete(self, key: str) -> None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return

        try:
            await self.redis_client.delete(key)
        except Exception as exc:
            logger.error("Cache delete error for {}: {}", key, str(exc))

    async def delete_pattern(self, pattern: str) -> None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return

        try:
            keys = [key async for key in self.redis_client.scan_iter(match=pattern)]
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Deleted {} cache keys for pattern {}", len(keys), pattern)
        except Exception as exc:
            logger.error("Cache delete pattern error for {}: {}", pattern, str(exc))

    async def exists(self, key: str) -> bool:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as exc:
            logger.error("Cache exists error for {}: {}", key, str(exc))
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return 0

        try:
            return int(await self.redis_client.incrby(key, amount))
        except Exception as exc:
            logger.error("Cache increment error for {}: {}", key, str(exc))
            return 0

    async def expire(self, key: str, ttl: int) -> None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None:
            return

        try:
            await self.redis_client.expire(key, ttl)
        except Exception as exc:
            logger.error("Cache expire error for {}: {}", key, str(exc))

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        if not self._connected:
            await self.connect()
        if self.redis_client is None or not keys:
            return {}

        try:
            values = await self.redis_client.mget(keys)
            result: dict[str, Any] = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = json.loads(value)
            return result
        except Exception as exc:
            logger.error("Cache get_many error: {}", str(exc))
            return {}

    async def set_many(self, data: dict[str, Any], ttl: int = 300) -> None:
        if not self._connected:
            await self.connect()
        if self.redis_client is None or not data:
            return

        try:
            pipe = self.redis_client.pipeline()
            for key, value in data.items():
                pipe.setex(key, ttl, json.dumps(self._serialize(value), default=str))
            await pipe.execute()
        except Exception as exc:
            logger.error("Cache set_many error: {}", str(exc))

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return {str(key): CacheService._serialize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [CacheService._serialize(item) for item in value]
        if isinstance(value, tuple):
            return [CacheService._serialize(item) for item in value]
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool)):
            return {
                key: CacheService._serialize(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return value

    @staticmethod
    def _track_cache_hit() -> None:
        try:
            from app.core.metrics import cache_hits

            cache_hits.inc()
        except Exception:
            pass

    @staticmethod
    def _track_cache_miss() -> None:
        try:
            from app.core.metrics import cache_misses

            cache_misses.inc()
        except Exception:
            pass

    @staticmethod
    def build_filters_hash(filters: NewsFilterParams) -> str:
        serialized = filters.model_dump(mode="json")
        return hashlib.md5(
            json.dumps(serialized, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    async def cache_news_list(self, filters: NewsFilterParams, data: Any, ttl: int = 300) -> None:
        filters_hash = self.build_filters_hash(filters)
        key = self.NEWS_LIST.format(filters_hash=filters_hash)
        await self.set(key, data, ttl)

    async def get_cached_news_list(self, filters: NewsFilterParams) -> Any | None:
        filters_hash = self.build_filters_hash(filters)
        key = self.NEWS_LIST.format(filters_hash=filters_hash)
        return await self.get(key)

    async def cache_news_detail(self, article_id: int, data: Any, ttl: int = 600) -> None:
        await self.set(self.NEWS_DETAIL.format(article_id=article_id), data, ttl)

    async def get_cached_news_detail(self, article_id: int) -> Any | None:
        return await self.get(self.NEWS_DETAIL.format(article_id=article_id))

    async def cache_trending_news(self, timeframe: str, data: Any, ttl: int = 300) -> None:
        await self.set(self.NEWS_TRENDING.format(timeframe=timeframe), data, ttl)

    async def get_cached_trending_news(self, timeframe: str) -> Any | None:
        return await self.get(self.NEWS_TRENDING.format(timeframe=timeframe))

    async def cache_featured_news(self, data: Any, ttl: int = 300) -> None:
        await self.set(self.NEWS_FEATURED, data, ttl)

    async def get_cached_featured_news(self) -> Any | None:
        return await self.get(self.NEWS_FEATURED)

    async def cache_market_symbol(self, symbol: str, data: Any, ttl: int = 60) -> None:
        await self.set(self.MARKET_SYMBOL.format(symbol=symbol.upper()), data, ttl)

    async def get_cached_market_symbol(self, symbol: str) -> Any | None:
        return await self.get(self.MARKET_SYMBOL.format(symbol=symbol.upper()))

    async def cache_market_real_estate(self, data: Any, ttl: int = 120) -> None:
        await self.set(self.MARKET_REAL_ESTATE, data, ttl)

    async def get_cached_market_real_estate(self) -> Any | None:
        return await self.get(self.MARKET_REAL_ESTATE)

    async def cache_analytics_trends(self, days: int, data: Any, ttl: int = 300) -> None:
        await self.set(self.ANALYTICS_TRENDS.format(days=days), data, ttl)

    async def get_cached_analytics_trends(self, days: int) -> Any | None:
        return await self.get(self.ANALYTICS_TRENDS.format(days=days))

    async def cache_analytics_sentiment(
        self,
        category: str | None,
        days: int,
        data: Any,
        ttl: int = 300,
    ) -> None:
        category_key = category or "all"
        await self.set(self.ANALYTICS_SENTIMENT.format(category=category_key, days=days), data, ttl)

    async def get_cached_analytics_sentiment(self, category: str | None, days: int) -> Any | None:
        category_key = category or "all"
        return await self.get(self.ANALYTICS_SENTIMENT.format(category=category_key, days=days))


cache = CacheService()


def _normalize_for_key(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _normalize_for_key(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_normalize_for_key(item) for item in value]
    if value.__class__.__name__ == "AsyncSession":
        return "async_session"
    return str(value)


def cache_key(*args: Any, **kwargs: Any) -> str:
    payload = {
        "args": [_normalize_for_key(arg) for arg in args],
        "kwargs": {key: _normalize_for_key(value) for key, value in sorted(kwargs.items())},
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{key_prefix}:{cache_key(*args, **kwargs)}" if key_prefix else cache_key(*args, **kwargs)
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug("Cache hit {}", key)
                return cached_value

            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator
