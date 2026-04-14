from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html import unescape
import math
import re
import statistics
from typing import Any

import feedparser
import httpx
import yfinance as yf
from dateutil import parser as date_parser
from loguru import logger

from app.config import get_settings
from app.core.circuit_breaker import CircuitBreakerOpenError, provider_health
from app.core.providers import provider_registry
from app.integrations.alpha_vantage_client import AlphaVantageClient
from app.integrations.news_clients import (
    BingNewsClient,
    CurrentsClient,
    GNewsClient,
    NewsAPIClient,
    NewsDataClient,
    RSSFeedParser,
)
from app.models.market_data import MarketType, StockExchange, WatchlistSymbol
from app.models.news import NewsCategory, NewsSource
from app.schemas.news import NewsArticleCreate
from app.tasks.scrapers.dubai_properties import DubaiPropertyScraper

settings = get_settings()


@dataclass
class NormalizedNewsRecord:
    title: str
    description: str | None
    content: str | None
    url: str
    source: NewsSource
    source_name: str
    source_provider: str
    author: str | None
    category: NewsCategory
    published_at: datetime
    image_url: str | None = None


@dataclass
class NormalizedMarketQuote:
    symbol: str
    alias_used: str
    name: str
    market_type: MarketType
    exchange: StockExchange | None
    price: float
    open_price: float | None
    high_price: float | None
    low_price: float | None
    previous_close: float | None
    volume: int
    market_cap: float | None
    change: float
    change_percent: float
    currency: str = "AED"
    provider: str = "unknown"
    supporting_providers: list[str] = field(default_factory=list)


@dataclass
class NormalizedCurrencyRate:
    from_currency: str
    to_currency: str
    rate: float
    timestamp: datetime
    source: str = "unknown"
    supporting_sources: list[str] = field(default_factory=list)


@dataclass
class NormalizedEconomicIndicator:
    indicator_name: str
    indicator_code: str
    value: float
    unit: str | None
    period: str | None
    timestamp: datetime
    source: str
    description: str | None


@dataclass
class NormalizedWeatherSnapshot:
    location_name: str
    latitude: float
    longitude: float
    temperature_c: float
    apparent_temperature_c: float | None
    humidity_percent: int | None
    wind_speed_kph: float | None
    weather_code: int | None
    weather_summary: str
    observed_at: datetime
    source: str = "open_meteo"


class FreeDataAggregator:
    RSS_FEEDS: dict[str, tuple[str, NewsSource, str]] = {
        "propertyfinder_blog": ("https://www.propertyfinder.ae/blog/feed/", NewsSource.MANUAL, "Property Finder Blog"),
        "bayut_blog": ("https://www.bayut.com/mybayut/feed/", NewsSource.MANUAL, "Bayut Blog"),
        "dubizzle_property": ("https://blog.dubizzle.com/property/feed/", NewsSource.MANUAL, "Dubizzle Property"),
        "gulf_news_property": ("https://gulfnews.com/business/property/rss", NewsSource.RSS_GULF_NEWS, "Gulf News Property"),
        "the_national_property": ("https://www.thenationalnews.com/business/property/rss/", NewsSource.RSS_THE_NATIONAL, "The National Property"),
        "khaleej_times_real_estate": ("https://www.khaleejtimes.com/real-estate/rss", NewsSource.RSS_KHALEEJ_TIMES, "Khaleej Times Real Estate"),
        "arabian_business_real_estate": ("https://www.arabianbusiness.com/industries/real-estate/rss", NewsSource.RSS_ARABIAN_BUSINESS, "Arabian Business Real Estate"),
        "construction_week": ("https://www.constructionweekonline.com/feed", NewsSource.MANUAL, "Construction Week"),
        "zawya_real_estate": ("https://www.zawya.com/en/rss/real-estate", NewsSource.MANUAL, "Zawya Real Estate"),
        "dubai_media_office": ("https://www.mediaoffice.ae/en/rss.xml", NewsSource.MANUAL, "Dubai Media Office"),
        "reuters_world_news": ("https://feeds.reuters.com/Reuters/worldNews", NewsSource.MANUAL, "Reuters World News"),
    }

    UAE_SYMBOL_ALIASES: dict[str, list[str]] = {
        "EMAAR": ["EMAAR.DU", "EMAAR:DFM", "EMAARDEV.AE", "EMAAR.AE", "EMAAR"],
        "DAMAC": ["DAMAC", "DAMAC.DU", "DAMAC:DFM", "DAMAC.AE"],
        "DEYAAR": ["DEYAAR.DU", "DEYAAR:DFM", "DEYAAR.AE", "DEYAAR"],
        "ALDAR": ["ALDAR", "ALDAR.AD", "ALDAR:ADX", "ALDAR.AE"],
        "AMLAK": ["AMLAK.DU", "AMLAK:DFM", "AMLAK.AE", "AMLAK"],
        "UPP": ["UPP.DU", "UPP:DFM", "UNIONPRO.AE", "UPP.AE", "UPP"],
        "ESHRAQ": ["ESHRAQ", "ESHRAQ.AD", "ESHRAQ:ADX", "ESHRAQ.AE"],
        "RAKPROP": ["RAKPROP", "RAKPROP.AE", "RAKPROP:ADX", "RAKPROP.AD"],
        "DFM": ["DFM.AE", "DFM.DU", "DFM:DFM", "DFM"],
        "DIC": ["DIC.AE", "DIC.DU", "DIC:DFM", "DIC"],
        "ADCB": ["ADCB.AB", "ADCB", "ADCB.AD", "ADCB:ADX"],
        "FAB": ["FAB", "FAB.AD", "FAB:ADX"],
        "ADNOC": ["ADNOCDIST", "ADNOCDIST.AD", "ADNOC.AD", "ADNOCDIST:ADX"],
        "^DFM": ["DFMGI.AE", "^DFMGI"],
    }

    STOCKANALYSIS_SYMBOL_OVERRIDES: dict[str, str] = {
        "ADNOC": "ADNOCDIST",
    }

    CURRENCY_PAIRS: list[tuple[str, str]] = [
        ("AED", "USD"),
        ("AED", "EUR"),
        ("AED", "GBP"),
        ("USD", "AED"),
        ("EUR", "AED"),
        ("GBP", "AED"),
    ]

    WORLD_BANK_INDICATORS: dict[str, str] = {
        "NY.GDP.MKTP.CD": "GDP (Current US$)",
        "FP.CPI.TOTL.ZG": "Inflation, Consumer Prices",
        "SL.UEM.TOTL.ZS": "Unemployment Rate",
        "NE.CON.PRVT.ZS": "Household Final Consumption Expenditure",
    }

    FRED_INDICATORS: dict[str, tuple[str, str]] = {
        "GDP": ("US GDP", "USA"),
        "CPIAUCSL": ("US Consumer Price Index", "USA"),
        "UNRATE": ("US Unemployment Rate", "USA"),
        "FEDFUNDS": ("US Federal Funds Rate", "USA"),
        "DGS10": ("US 10Y Treasury Yield", "USA"),
    }

    DUBAI_OPEN_DATASETS: dict[str, dict[str, str]] = {
        "real_estate_transactions": {"url": "https://www.dubaipulse.gov.ae/data/dld-transactions/", "description": "Dubai Land Department transactions dataset landing page"},
        "property_price_index": {"url": "https://www.dubaipulse.gov.ae/data/reidin-property-price/", "description": "Dubai property price index dataset landing page"},
        "building_permits": {"url": "https://www.dubaipulse.gov.ae/data/dm-building-permits/", "description": "Dubai Municipality building permits dataset landing page"},
        "tourism_stats": {"url": "https://www.dubaipulse.gov.ae/data/dtcm-tourism/", "description": "Tourism statistics impacting rental demand"},
    }

    OPEN_METEO_LOCATIONS: dict[str, tuple[float, float]] = {
        "Dubai": (25.2048, 55.2708),
        "Abu Dhabi": (24.4539, 54.3773),
        "Riyadh": (24.7136, 46.6753),
    }

    WEATHER_CODE_SUMMARIES: dict[int, str] = {
        0: "Clear",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        80: "Rain showers",
        95: "Thunderstorm",
    }

    LOCATION_TERMS = ("dubai", "uae", "abu dhabi", "emirates", "dfm", "adx")
    PROPERTY_TERMS = ("property", "real estate", "housing", "villa", "apartment", "rental", "rent", "mortgage", "developer", "off-plan", "residential", "commercial", "construction")

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "DUBNEWSAI/1.0 (+https://dubnewsai.com; Dubai real estate intelligence platform)"},
        )
        self._dfm_stock_cache: tuple[datetime, dict[str, dict[str, Any]]] | None = None

    async def close(self) -> None:
        await self.client.aclose()

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            parsed = date_parser.parse(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def _clean_text(value: str | None, max_length: int | None = None) -> str | None:
        if not value:
            return None
        cleaned = " ".join(str(value).split()).strip()
        if not cleaned:
            return None
        return cleaned[:max_length] if max_length else cleaned

    @staticmethod
    def _normalize_url(value: str | None) -> str | None:
        cleaned = FreeDataAggregator._clean_text(value)
        if cleaned and cleaned.startswith(("http://", "https://")):
            return cleaned
        return None

    @classmethod
    def _looks_relevant(cls, *chunks: str | None) -> bool:
        text = " ".join(chunk or "" for chunk in chunks).lower()
        return any(term in text for term in cls.LOCATION_TERMS) and any(term in text for term in cls.PROPERTY_TERMS)

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            if value in (None, "", "None"):
                return None
            parsed = float(str(value).replace("%", "").replace(",", ""))
            if not math.isfinite(parsed):
                return None
            return parsed
        except Exception:
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            if value in (None, "", "None"):
                return 0
            return int(float(str(value).replace(",", "").strip()))
        except Exception:
            return 0

    @staticmethod
    def _category_from_text(title: str, description: str | None = None) -> NewsCategory:
        text = f"{title} {description or ''}".lower()
        keyword_map = {
            NewsCategory.REAL_ESTATE: ["property", "real estate", "rental", "villa", "apartment", "developer"],
            NewsCategory.MARKET: ["bond", "stock", "shares", "dfm", "adx", "index"],
            NewsCategory.ECONOMY: ["gdp", "inflation", "economy", "consumption", "employment"],
            NewsCategory.REGULATION: ["law", "regulation", "policy", "permit", "authority"],
            NewsCategory.DEVELOPMENT: ["development", "construction", "project", "launch"],
            NewsCategory.INFRASTRUCTURE: ["transport", "metro", "airport", "road"],
        }
        scores = {category: sum(1 for keyword in keywords if keyword in text) for category, keywords in keyword_map.items()}
        best = max(scores, key=scores.get, default=NewsCategory.GENERAL)
        return best if scores.get(best, 0) > 0 else NewsCategory.GENERAL

    @staticmethod
    def _dedupe_news(records: list[NormalizedNewsRecord]) -> list[NormalizedNewsRecord]:
        deduped: dict[str, NormalizedNewsRecord] = {}
        for record in sorted(records, key=lambda item: item.published_at, reverse=True):
            deduped.setdefault(record.url, record)
        return list(deduped.values())

    async def _request_json(self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def _records_from_client_articles(
        self,
        articles: list[dict[str, Any]],
        *,
        source: NewsSource,
        source_provider: str,
        fallback_source_name: str,
    ) -> list[NormalizedNewsRecord]:
        records: list[NormalizedNewsRecord] = []
        for article in articles[: settings.NEWS_PROVIDER_ARTICLE_LIMIT]:
            url = self._normalize_url(article.get("url"))
            if not url:
                continue
            records.append(
                NormalizedNewsRecord(
                    title=self._clean_text(article.get("title"), 500) or "Untitled",
                    description=self._clean_text(article.get("description"), 5000),
                    content=self._clean_text(article.get("content"), 50000),
                    url=url,
                    source=source,
                    source_name=self._clean_text(article.get("source"), 200) or fallback_source_name,
                    source_provider=source_provider,
                    author=self._clean_text(article.get("author"), 200),
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("published_at")),
                    image_url=self._normalize_url(article.get("image_url")),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    @staticmethod
    def _summarize_body(value: str | None, limit: int = 360) -> str | None:
        cleaned = FreeDataAggregator._clean_text(value, 6000)
        if not cleaned:
            return None
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", cleaned)
        summary = " ".join(sentence.strip() for sentence in sentences[:2] if sentence.strip()).strip()
        if not summary:
            summary = cleaned[:limit]
        return summary[:limit].rstrip()

    @staticmethod
    def _default_news_query(query: str | None = None) -> str:
        return query or "Dubai real estate"

    @staticmethod
    def _news_query_variants(query: str | None = None) -> list[str]:
        if query:
            return [query]
        return [
            "Dubai real estate",
            "Dubai property",
            "UAE property market",
            "Emaar Aldar Damac",
        ]

    async def _fetch_newsapi(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.NEWSAPI_KEY:
            return []
        client = NewsAPIClient()
        try:
            articles = await client.search_news(
                self._default_news_query(query),
                max_age_hours=settings.NEWS_LOOKBACK_DAYS * 24,
                max_results=min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2),
            )
        finally:
            await client.close()
        return self._records_from_client_articles(
            articles,
            source=NewsSource.NEWSAPI,
            source_provider="newsapi",
            fallback_source_name="NewsAPI",
        )

    async def _fetch_gnews(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.GNEWS_API_KEY:
            return []
        client = GNewsClient()
        try:
            articles = await client.search_news(
                self._default_news_query(query),
                max_age_hours=settings.NEWS_LOOKBACK_DAYS * 24,
                max_results=settings.NEWS_PROVIDER_ARTICLE_LIMIT,
            )
        finally:
            await client.close()
        return self._records_from_client_articles(
            articles,
            source=NewsSource.RAPID_API,
            source_provider="gnews",
            fallback_source_name="GNews",
        )

    async def _fetch_currents(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.CURRENTS_API_KEY:
            return []
        client = CurrentsClient()
        try:
            articles = await client.search_news(
                self._default_news_query(query),
                max_age_hours=settings.NEWS_LOOKBACK_DAYS * 24,
                max_results=settings.NEWS_PROVIDER_ARTICLE_LIMIT,
            )
        finally:
            await client.close()
        return self._records_from_client_articles(
            articles,
            source=NewsSource.RAPID_API,
            source_provider="currents",
            fallback_source_name="Currents",
        )

    async def _fetch_newsdata(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.NEWSDATA_API_KEY:
            return []
        client = NewsDataClient()
        try:
            articles = await client.search_news(
                self._default_news_query(query),
                max_results=settings.NEWS_PROVIDER_ARTICLE_LIMIT,
            )
        finally:
            await client.close()
        return self._records_from_client_articles(
            articles,
            source=NewsSource.RAPID_API,
            source_provider="newsdata",
            fallback_source_name="NewsData.io",
        )

    async def _fetch_thenewsapi(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.THENEWSAPI_KEY:
            return []
        records: list[NormalizedNewsRecord] = []
        for candidate_query in self._news_query_variants(query):
            try:
                payload = await self._request_json(
                    "https://api.thenewsapi.com/v1/news/all",
                    params={
                        "api_token": settings.THENEWSAPI_KEY,
                        "search": candidate_query,
                        "search_fields": "title,description,keywords",
                        "language": "en",
                        "limit": min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2),
                        "sort": "published_at",
                    },
                )
            except Exception as exc:
                logger.debug("TheNewsAPI fetch failed for query {}: {}", candidate_query, str(exc))
                continue
            for article in payload.get("data", [])[: min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2)]:
                url = self._normalize_url(article.get("url"))
                if not url:
                    continue
                description = self._clean_text(article.get("description"), 5000)
                title = self._clean_text(article.get("title"), 500) or "Untitled"
                records.append(
                    NormalizedNewsRecord(
                        title=title,
                        description=description,
                        content=self._clean_text(article.get("snippet"), 50000) or description,
                        url=url,
                        source=NewsSource.RAPID_API,
                        source_name=self._clean_text(article.get("source"), 200) or "TheNewsAPI",
                        source_provider="thenewsapi",
                        author=self._clean_text(article.get("author"), 200),
                        category=self._category_from_text(title, description),
                        published_at=self._parse_datetime(article.get("published_at")),
                        image_url=self._normalize_url(article.get("image_url")),
                    )
                )
            if records:
                break
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_mediastack(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.MEDIASTACK_API_KEY:
            return []
        records: list[NormalizedNewsRecord] = []
        for candidate_query in self._news_query_variants(query):
            try:
                payload = await self._request_json(
                    "http://api.mediastack.com/v1/news",
                    params={
                        "access_key": settings.MEDIASTACK_API_KEY,
                        "keywords": candidate_query,
                        "languages": "en",
                        "countries": "ae",
                        "sort": "published_desc",
                        "limit": min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2),
                    },
                )
            except Exception as exc:
                logger.debug("Mediastack fetch failed for query {}: {}", candidate_query, str(exc))
                continue
            for article in payload.get("data", [])[: min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2)]:
                url = self._normalize_url(article.get("url"))
                if not url:
                    continue
                description = self._clean_text(article.get("description"), 5000)
                title = self._clean_text(article.get("title"), 500) or "Untitled"
                records.append(
                    NormalizedNewsRecord(
                        title=title,
                        description=description,
                        content=description,
                        url=url,
                        source=NewsSource.RAPID_API,
                        source_name=self._clean_text(article.get("source"), 200) or "Mediastack",
                        source_provider="mediastack",
                        author=self._clean_text(article.get("author"), 200),
                        category=self._category_from_text(title, description),
                        published_at=self._parse_datetime(article.get("published_at")),
                        image_url=self._normalize_url(article.get("image")),
                    )
                )
            if records:
                break
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_newsapi_ai(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.NEWSAPI_AI_KEY:
            return []
        records: list[NormalizedNewsRecord] = []
        for candidate_query in self._news_query_variants(query):
            try:
                response = await self.client.post(
                    "https://eventregistry.org/api/v1/article/getArticles",
                    json={
                        "apiKey": settings.NEWSAPI_AI_KEY,
                        "resultType": "articles",
                        "articlesSortBy": "date",
                        "articlesCount": min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2),
                        "query": {
                            "$query": {
                                "lang": "eng",
                                "keyword": candidate_query,
                            },
                            "$filter": {
                                "forceMaxDataTimeWindow": str(max(settings.NEWS_LOOKBACK_DAYS, 31)),
                            },
                        },
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                logger.debug("NewsAPI.ai fetch failed for query {}: {}", candidate_query, str(exc))
                continue
            for article in payload.get("articles", {}).get("results", [])[: min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2)]:
                url = self._normalize_url(article.get("url"))
                if not url:
                    continue
                title = self._clean_text(article.get("title"), 500) or "Untitled"
                body = self._clean_text(article.get("body"), 50000)
                description = self._summarize_body(body)
                source_title = None
                source = article.get("source")
                if isinstance(source, dict):
                    source_title = source.get("title")
                records.append(
                    NormalizedNewsRecord(
                        title=title,
                        description=description,
                        content=body,
                        url=url,
                        source=NewsSource.RAPID_API,
                        source_name=self._clean_text(source_title, 200) or "NewsAPI.ai",
                        source_provider="newsapi_ai",
                        author=self._clean_text(", ".join(author.get("name", "") for author in article.get("authors", []) if author.get("name")), 200),
                        category=self._category_from_text(title, description),
                        published_at=self._parse_datetime(article.get("dateTimePub") or article.get("dateTime")),
                        image_url=self._normalize_url(article.get("image")),
                    )
                )
            if records:
                break
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_bing_news(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        if not settings.BING_NEWS_API_KEY:
            return []
        client = BingNewsClient()
        try:
            articles = await client.search_news(
                self._default_news_query(query),
                max_age_hours=settings.NEWS_LOOKBACK_DAYS * 24,
                max_results=settings.NEWS_PROVIDER_ARTICLE_LIMIT,
            )
        finally:
            await client.close()
        return self._records_from_client_articles(
            articles,
            source=NewsSource.RAPID_API,
            source_provider="bing_news",
            fallback_source_name="Bing News",
        )

    async def _fetch_contextual_web(self, query: str | None = None) -> list[NormalizedNewsRecord]:
        rapid_api_key = settings.CONTEXTUAL_WEB_API_KEY or settings.RAPID_API_KEY
        if not rapid_api_key:
            return []
        endpoints = [
            (
                "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI",
                {
                    "q": self._default_news_query(query),
                    "pageNumber": 1,
                    "pageSize": settings.NEWS_PROVIDER_ARTICLE_LIMIT,
                    "autoCorrect": True,
                    "withThumbnails": True,
                    "fromPublishedDate": (datetime.now(timezone.utc) - timedelta(days=settings.NEWS_LOOKBACK_DAYS)).isoformat(),
                },
                {
                    "X-RapidAPI-Key": rapid_api_key,
                    "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
                },
                "value",
            ),
            (
                "https://real-time-web-search.p.rapidapi.com/search-news",
                {
                    "query": self._default_news_query(query),
                    "limit": settings.NEWS_PROVIDER_ARTICLE_LIMIT,
                    "time": "w",
                },
                {
                    "X-RapidAPI-Key": rapid_api_key,
                    "X-RapidAPI-Host": "real-time-web-search.p.rapidapi.com",
                },
                "data",
            ),
        ]

        for endpoint, params, headers, items_key in endpoints:
            try:
                payload = await self._request_json(endpoint, params=params, headers=headers)
            except Exception as exc:
                logger.debug("RapidAPI news endpoint {} failed: {}", endpoint, str(exc))
                continue

            records: list[NormalizedNewsRecord] = []
            for article in payload.get(items_key, []):
                url = self._normalize_url(article.get("url") or article.get("link"))
                if not url:
                    continue
                image = article.get("image")
                records.append(
                    NormalizedNewsRecord(
                        title=self._clean_text(article.get("title"), 500) or "Untitled",
                        description=self._clean_text(article.get("description") or article.get("snippet"), 5000),
                        content=self._clean_text(article.get("body") or article.get("snippet"), 50000),
                        url=url,
                        source=NewsSource.RAPID_API,
                        source_name="RapidAPI News Search",
                        source_provider="contextual_web",
                        author=self._clean_text(article.get("author"), 200),
                        category=self._category_from_text(article.get("title", ""), article.get("description") or article.get("snippet")),
                        published_at=self._parse_datetime(article.get("datePublished") or article.get("published") or article.get("published_datetime_utc")),
                        image_url=self._normalize_url(image.get("url")) if isinstance(image, dict) else self._normalize_url(article.get("thumbnail")),
                    )
                )
            relevant_records = [record for record in records if self._looks_relevant(record.title, record.description, record.content)]
            if relevant_records:
                return relevant_records

        return []

    async def _fetch_single_rss_feed(self, feed_name: str, feed_url: str, source: NewsSource, source_name: str) -> list[NormalizedNewsRecord]:
        parser = RSSFeedParser()
        try:
            entries = await parser.parse_feed(
                feed_url,
                max_age_hours=settings.NEWS_LOOKBACK_DAYS * 24,
                max_results=settings.NEWS_PROVIDER_ARTICLE_LIMIT,
            )
            records: list[NormalizedNewsRecord] = []
            for entry in entries:
                url = self._normalize_url(entry.get("url"))
                if not url:
                    continue
                summary = self._clean_text(entry.get("description"), 5000)
                title = self._clean_text(entry.get("title"), 500) or "Untitled"
                records.append(
                    NormalizedNewsRecord(
                        title=title,
                        description=summary,
                        content=self._clean_text(entry.get("content"), 50000) or summary,
                        url=url,
                        source=source,
                        source_name=source_name,
                        source_provider=f"rss_{feed_name}",
                        author=self._clean_text(entry.get("author"), 200),
                        category=self._category_from_text(title, summary),
                        published_at=self._parse_datetime(entry.get("published_at")),
                        image_url=self._normalize_url(entry.get("image_url")),
                    )
                )
            return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]
        except Exception as exc:
            logger.warning("RSS source {} unavailable: {}", feed_name, str(exc))
            return []
        finally:
            await parser.close()

    async def _fetch_rss(self) -> list[NormalizedNewsRecord]:
        tasks = [
            self._fetch_single_rss_feed(feed_name, url, source, source_name)
            for feed_name, (url, source, source_name) in self.RSS_FEEDS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        records: list[NormalizedNewsRecord] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            records.extend(result)
        return records

    async def _fetch_scraped_news(self) -> list[NormalizedNewsRecord]:
        scraper = DubaiPropertyScraper()
        try:
            insights = await scraper.fetch_all()
        finally:
            await scraper.close()

        records: list[NormalizedNewsRecord] = []
        for insight in insights[: max(10, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2)]:
            url = self._normalize_url(insight.url)
            if not url:
                continue
            records.append(
                NormalizedNewsRecord(
                    title=insight.title,
                    description=insight.excerpt,
                    content=insight.excerpt,
                    url=url,
                    source=NewsSource.MANUAL,
                    source_name=insight.source_name,
                    source_provider=f"scraper_{insight.source_name.lower().replace(' ', '_')}",
                    author=None,
                    category=self._category_from_text(insight.title, insight.excerpt),
                    published_at=insight.published_at,
                    image_url=self._normalize_url(insight.image_url),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def fetch_news_articles(
        self,
        *,
        include_api: bool = True,
        include_rss: bool = True,
        include_scraped: bool = True,
        query: str | None = None,
    ) -> list[NewsArticleCreate]:
        jobs: list[Any] = []
        if include_api:
            jobs.extend(
                [
                    self._fetch_newsapi(query=query),
                    self._fetch_gnews(query=query),
                    self._fetch_currents(query=query),
                    self._fetch_newsdata(query=query),
                    self._fetch_thenewsapi(query=query),
                    self._fetch_mediastack(query=query),
                    self._fetch_newsapi_ai(query=query),
                    self._fetch_bing_news(query=query),
                    self._fetch_contextual_web(query=query),
                ]
            )
        if include_rss:
            jobs.append(self._fetch_rss())
        if include_scraped:
            jobs.append(self._fetch_scraped_news())

        results = await asyncio.gather(*jobs, return_exceptions=True)
        records: list[NormalizedNewsRecord] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("News provider failed: {}", str(result))
                continue
            records.extend(result)

        articles: list[NewsArticleCreate] = []
        for record in self._dedupe_news(records):
            try:
                articles.append(
                    NewsArticleCreate(
                        title=record.title,
                        description=record.description,
                        content=record.content,
                        url=record.url,
                        source=record.source,
                        source_name=record.source_name,
                        author=record.author,
                        category=record.category,
                        published_at=record.published_at,
                        image_url=record.image_url,
                    )
                )
            except Exception as exc:
                logger.debug("Skipping normalized news record {}: {}", record.url, str(exc))
        return articles

    def _build_symbol_aliases(self, watchlist_symbols: list[WatchlistSymbol]) -> tuple[dict[str, list[str]], list[str]]:
        aliases_by_symbol: dict[str, list[str]] = {}
        all_aliases: list[str] = []
        for item in watchlist_symbols:
            aliases = self.UAE_SYMBOL_ALIASES.get(item.symbol.upper(), [item.symbol.upper()])
            ordered_aliases = [*aliases, item.symbol.upper()]
            deduped = list(dict.fromkeys(alias.upper() for alias in ordered_aliases))
            aliases_by_symbol[item.symbol.upper()] = deduped
            for alias in deduped:
                if alias not in all_aliases:
                    all_aliases.append(alias)
        return aliases_by_symbol, all_aliases

    @staticmethod
    def _registry_provider_name(provider_name: str) -> str:
        aliases = {
            "yahoo_chart": "yahoo_finance",
        }
        return aliases.get(provider_name, provider_name)

    @classmethod
    def _stockanalysis_exchange_slug(cls, exchange: StockExchange | None) -> str | None:
        if exchange == StockExchange.ADX:
            return "adx"
        if exchange == StockExchange.DFM:
            return "dfm"
        return None

    @staticmethod
    def _is_provider_enabled(provider_name: str) -> bool:
        provider = provider_registry.get_provider(FreeDataAggregator._registry_provider_name(provider_name))
        return bool(provider.enabled) if provider is not None else False

    @staticmethod
    def _provider_priority(provider_name: str) -> tuple[int, float]:
        provider = provider_registry.get_provider(FreeDataAggregator._registry_provider_name(provider_name))
        if provider is None:
            return (99, 0.0)
        priority = int(provider.priority.value if hasattr(provider.priority, "value") else provider.priority)
        return (priority, float(provider.reliability_score or 0.0))

    @staticmethod
    def _default_currency_for_watchlist(watchlist: WatchlistSymbol) -> str:
        if watchlist.exchange in {StockExchange.DFM, StockExchange.ADX}:
            return "AED"
        if watchlist.market_type == MarketType.COMMODITY:
            return "USD"
        if watchlist.symbol.upper() == "^FTSE":
            return "GBP"
        if watchlist.symbol.upper() == "^N225":
            return "JPY"
        if watchlist.symbol.upper() == "^HSI":
            return "HKD"
        return "USD"

    @staticmethod
    def _quote_completeness_score(quote: NormalizedMarketQuote) -> int:
        optional_values = [
            quote.open_price,
            quote.high_price,
            quote.low_price,
            quote.previous_close,
            quote.market_cap,
        ]
        return sum(1 for value in optional_values if value not in (None, 0)) + (1 if quote.volume else 0)

    @classmethod
    def _pick_primary_quote(cls, quotes: list[NormalizedMarketQuote]) -> NormalizedMarketQuote:
        return min(
            quotes,
            key=lambda quote: (
                cls._provider_priority(quote.provider)[0],
                -cls._provider_priority(quote.provider)[1],
                -cls._quote_completeness_score(quote),
                quote.alias_used,
            ),
        )

    @classmethod
    def _pick_primary_currency_rate(cls, rates: list[NormalizedCurrencyRate]) -> NormalizedCurrencyRate:
        return min(
            rates,
            key=lambda rate: (
                cls._provider_priority(rate.source)[0],
                -cls._provider_priority(rate.source)[1],
                -rate.timestamp.timestamp(),
            ),
        )

    @classmethod
    def _merge_currency_rates_for_pair(cls, rates: list[NormalizedCurrencyRate]) -> NormalizedCurrencyRate:
        primary = cls._pick_primary_currency_rate(rates)
        consensus_values = [rate.rate for rate in rates if rate.rate > 0]
        consensus_rate = statistics.median(consensus_values) if consensus_values else primary.rate
        latest_timestamp = max(rate.timestamp for rate in rates)
        supporting_sources = list(
            dict.fromkeys(rate.source for rate in rates if rate.source and rate.source != primary.source)
        )
        return NormalizedCurrencyRate(
            from_currency=primary.from_currency,
            to_currency=primary.to_currency,
            rate=consensus_rate,
            timestamp=latest_timestamp,
            source=primary.source,
            supporting_sources=supporting_sources,
        )

    @staticmethod
    def _select_validation_candidates(watchlist_symbols: list[WatchlistSymbol]) -> list[WatchlistSymbol]:
        segment_limits = {
            "uae": 6,
            "global": 4,
            "indices": 3,
            "commodities": 3,
        }
        selected: list[WatchlistSymbol] = []
        usage: dict[str, int] = {key: 0 for key in segment_limits}

        def resolve_segment(item: WatchlistSymbol) -> str:
            if item.market_type == MarketType.INDEX:
                return "indices"
            if item.market_type == MarketType.COMMODITY:
                return "commodities"
            if item.exchange in {StockExchange.DFM, StockExchange.ADX}:
                return "uae"
            return "global"

        for item in sorted(watchlist_symbols, key=lambda record: record.priority, reverse=True):
            segment = resolve_segment(item)
            if usage[segment] >= segment_limits[segment]:
                continue
            usage[segment] += 1
            selected.append(item)
        return selected

    def _enabled_quote_fetchers(self, *, include_yahoo_chart: bool = True) -> list[tuple[str, Any]]:
        fetchers: list[tuple[str, Any]] = []
        fetchers.append(("stockanalysis_market", self._fetch_stockanalysis_quote))
        fetchers.append(("dfm_marketwatch", self._fetch_dfm_marketwatch_quote))
        if include_yahoo_chart and self._is_provider_enabled("yahoo_finance"):
            fetchers.append(("yahoo_chart", self._fetch_yahoo_chart_quote))
        for provider_name, fetcher in [
            ("twelve_data", self._fetch_twelve_data_quote),
            ("finnhub", self._fetch_finnhub_quote),
            ("financial_modeling_prep", self._fetch_fmp_quote),
            ("alpha_vantage", self._fetch_alpha_vantage_quote),
            ("marketstack", self._fetch_marketstack_quote),
        ]:
            if self._is_provider_enabled(provider_name):
                fetchers.append((provider_name, fetcher))
        return fetchers

    async def _download_yahoo_history(self, aliases: list[str]) -> Any:
        def _download() -> Any:
            return yf.download(
                tickers=aliases,
                period="5d",
                interval="1d",
                auto_adjust=False,
                progress=False,
                group_by="ticker",
                threads=False,
            )

        return await asyncio.to_thread(_download)

    async def _fetch_yahoo_chart_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        payload = await self._request_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{alias}",
            params={"interval": "1d", "range": "5d", "includePrePost": "false"},
        )
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            return None

        meta = result[0].get("meta") or {}
        indicators = ((result[0].get("indicators") or {}).get("quote") or [{}])[0]
        closes = (indicators.get("close") or []) or []
        opens = (indicators.get("open") or []) or []
        highs = (indicators.get("high") or []) or []
        lows = (indicators.get("low") or []) or []
        volumes = (indicators.get("volume") or []) or []
        timestamps = result[0].get("timestamp") or []

        if not timestamps or not closes:
            return None

        valid_indices = [index for index, close_value in enumerate(closes) if self._safe_float(close_value) not in (None, 0)]
        if not valid_indices:
            return None

        last_index = valid_indices[-1]
        previous_index = valid_indices[-2] if len(valid_indices) > 1 else last_index
        price = self._safe_float(closes[last_index])
        previous_close = self._safe_float(closes[previous_index])
        if price is None or price <= 0:
            return None

        change = price - previous_close if previous_close not in (None, 0) else 0.0
        change_percent = (change / previous_close) * 100 if previous_close not in (None, 0) else 0.0

        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=self._safe_float(opens[last_index]) if len(opens) > last_index else None,
            high_price=self._safe_float(highs[last_index]) if len(highs) > last_index else None,
            low_price=self._safe_float(lows[last_index]) if len(lows) > last_index else None,
            previous_close=previous_close,
            volume=self._safe_int(volumes[last_index]) if len(volumes) > last_index else 0,
            market_cap=self._safe_float(meta.get("marketCap")),
            change=change,
            change_percent=change_percent,
            currency=str(meta.get("currency") or self._default_currency_for_watchlist(watchlist)),
            provider="yahoo_chart",
        )

    @staticmethod
    def _extract_yahoo_frame(history: Any, alias: str, alias_count: int) -> Any | None:
        if history is None or getattr(history, "empty", True):
            return None
        columns = getattr(history, "columns", None)
        if columns is None:
            return None
        nlevels = getattr(columns, "nlevels", 1)
        if nlevels > 1:
            top_level = columns.get_level_values(0)
            if alias not in top_level:
                return None
            frame = history[alias]
        else:
            if alias_count != 1:
                return None
            frame = history
        if frame is None or getattr(frame, "empty", True):
            return None
        cleaned = frame.dropna(how="all")
        return cleaned if not cleaned.empty else None

    def _build_quote_from_history(self, watchlist: WatchlistSymbol, alias: str, frame: Any) -> NormalizedMarketQuote | None:
        if frame is None or getattr(frame, "empty", True):
            return None

        last_row = frame.iloc[-1]
        previous_row = frame.iloc[-2] if len(frame.index) > 1 else None
        price = self._safe_float(last_row.get("Close"))
        open_price = self._safe_float(last_row.get("Open"))
        high_price = self._safe_float(last_row.get("High"))
        low_price = self._safe_float(last_row.get("Low"))
        previous_close = self._safe_float(previous_row.get("Close")) if previous_row is not None else self._safe_float(last_row.get("Close"))

        if price is None or price <= 0:
            return None

        change = price - previous_close if previous_close is not None else 0.0
        change_percent = (change / previous_close) * 100 if previous_close not in (None, 0) else 0.0
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            previous_close=previous_close,
            volume=self._safe_int(last_row.get("Volume")),
            market_cap=None,
            change=change,
            change_percent=change_percent,
            currency=self._default_currency_for_watchlist(watchlist),
            provider="yahoo_finance",
        )

    async def _fetch_yahoo_quotes(self, watchlist_symbols: list[WatchlistSymbol]) -> list[NormalizedMarketQuote]:
        if not watchlist_symbols:
            return []
        aliases_by_symbol, _ = self._build_symbol_aliases(watchlist_symbols)
        yahoo_aliases = [aliases_by_symbol[item.symbol.upper()][0] for item in watchlist_symbols if aliases_by_symbol.get(item.symbol.upper())]
        try:
            history = await provider_health.call_provider(
                "yahoo_finance",
                lambda: self._download_yahoo_history(yahoo_aliases),
            )
        except Exception as exc:
            logger.warning("Yahoo Finance batch download failed: {}", str(exc))
            history = None

        quotes: list[NormalizedMarketQuote] = []
        existing_symbols: set[str] = set()
        for item in watchlist_symbols:
            alias = aliases_by_symbol[item.symbol.upper()][0]
            frame = self._extract_yahoo_frame(history, alias, len(yahoo_aliases))
            quote = self._build_quote_from_history(item, alias, frame)
            if quote is not None:
                quotes.append(quote)
                existing_symbols.add(item.symbol.upper())

        for item in watchlist_symbols:
            if item.symbol.upper() in existing_symbols:
                continue
            for alias in aliases_by_symbol[item.symbol.upper()]:
                try:
                    quote = await provider_health.call_provider(
                        "yahoo_finance",
                        lambda item=item, alias=alias: self._fetch_yahoo_chart_quote(item, alias),
                    )
                except Exception as exc:
                    logger.debug("Yahoo chart quote failed for {} via {}: {}", item.symbol, alias, str(exc))
                    continue
                if quote is not None:
                    quotes.append(quote)
                    existing_symbols.add(item.symbol.upper())
                    break
        return quotes

    async def _get_dfm_marketwatch_quotes(self) -> dict[str, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if self._dfm_stock_cache and (now - self._dfm_stock_cache[0]) < timedelta(seconds=45):
            return self._dfm_stock_cache[1]

        payload = await self._request_json("https://api2.dfm.ae/mw/v1/stocks")
        rows: list[dict[str, Any]] = payload if isinstance(payload, list) else list(payload.get("data", []) or [])
        mapping = {
            str(item.get("id") or "").upper(): item
            for item in rows
            if str(item.get("id") or "").strip()
        }
        self._dfm_stock_cache = (now, mapping)
        return mapping

    async def _fetch_dfm_marketwatch_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if watchlist.exchange != StockExchange.DFM:
            return None

        quotes = await self._get_dfm_marketwatch_quotes()
        for candidate in (alias.upper(), watchlist.symbol.upper()):
            row = quotes.get(candidate)
            if row is None:
                continue

            price = (
                self._safe_float(row.get("lastradeprice"))
                or self._safe_float(row.get("lastsessionprice"))
                or self._safe_float(row.get("referenceprice"))
            )
            previous_close = self._safe_float(row.get("previousclosingprice")) or self._safe_float(row.get("referenceprice"))
            if price is None or price <= 0:
                continue

            change = self._safe_float(row.get("netchange"))
            if change is None and previous_close not in (None, 0):
                change = price - previous_close

            change_percent = self._safe_float(row.get("changepercentage"))
            if change_percent is None and previous_close not in (None, 0):
                change_percent = ((price - previous_close) / previous_close) * 100

            timestamp = self._parse_datetime(row.get("modificationdate"))
            return NormalizedMarketQuote(
                symbol=watchlist.symbol.upper(),
                alias_used=candidate,
                name=watchlist.name,
                market_type=watchlist.market_type,
                exchange=watchlist.exchange,
                price=price,
                open_price=self._safe_float(row.get("openingprice")),
                high_price=self._safe_float(row.get("highestprice")),
                low_price=self._safe_float(row.get("lowestprice")),
                previous_close=previous_close,
                volume=self._safe_int(row.get("totalvolume")),
                market_cap=self._safe_float(row.get("capital")),
                change=change or 0.0,
                change_percent=change_percent or 0.0,
                currency=self._default_currency_for_watchlist(watchlist),
                provider="dfm_marketwatch",
            )

        return None

    @classmethod
    def _extract_stockanalysis_metric(cls, html: str, label: str) -> str | None:
        pattern = re.compile(
            rf">\s*{re.escape(label)}\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(html)
        if not match:
            return None
        return unescape(match.group(1)).strip()

    @classmethod
    def _extract_stockanalysis_header(cls, html: str) -> tuple[float | None, float | None, float | None]:
        price_match = re.search(
            r'<div class="text-4xl font-bold[^"]*">\s*([\d.,]+)\s*</div>',
            html,
            re.IGNORECASE,
        )
        if not price_match:
            return None, None, None

        change_match = re.search(
            r'<div class="font-semibold[^"]*">\s*([+\-]?[\d.,]+)\s*\(([+\-]?[\d.,]+)%\)\s*</div>',
            html,
            re.IGNORECASE,
        )
        return (
            cls._safe_float(price_match.group(1)),
            cls._safe_float(change_match.group(1)) if change_match else None,
            cls._safe_float(change_match.group(2)) if change_match else None,
        )

    async def _fetch_stockanalysis_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        exchange_slug = self._stockanalysis_exchange_slug(watchlist.exchange)
        if exchange_slug is None:
            return None

        symbol_slug = self.STOCKANALYSIS_SYMBOL_OVERRIDES.get(watchlist.symbol.upper(), watchlist.symbol.upper())
        url = f"https://stockanalysis.com/quote/{exchange_slug}/{symbol_slug}/"
        response = await self.client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        html = response.text

        price, change, change_percent = self._extract_stockanalysis_header(html)
        if price is None or price <= 0:
            return None

        currency_match = re.search(r"Currency is ([A-Z]{3})", html)
        currency = currency_match.group(1) if currency_match else self._default_currency_for_watchlist(watchlist)
        open_price = self._safe_float(self._extract_stockanalysis_metric(html, "Open"))
        previous_close = self._safe_float(self._extract_stockanalysis_metric(html, "Previous Close"))
        day_range = self._extract_stockanalysis_metric(html, "Day's Range") or self._extract_stockanalysis_metric(html, "Day Range")
        high_price = None
        low_price = None
        if day_range and " - " in day_range:
            low_raw, high_raw = (part.strip() for part in day_range.split(" - ", 1))
            low_price = self._safe_float(low_raw)
            high_price = self._safe_float(high_raw)

        if change is None and previous_close not in (None, 0):
            change = price - previous_close
        if change_percent is None and previous_close not in (None, 0):
            change_percent = ((price - previous_close) / previous_close) * 100

        volume = self._safe_int(self._extract_stockanalysis_metric(html, "Volume"))
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            previous_close=previous_close,
            volume=volume,
            market_cap=None,
            change=change or 0.0,
            change_percent=change_percent or 0.0,
            currency=currency,
            provider="stockanalysis_market",
        )

    async def _fetch_twelve_data_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.TWELVE_DATA_API_KEY:
            return None
        payload = await self._request_json("https://api.twelvedata.com/quote", params={"symbol": alias, "apikey": settings.TWELVE_DATA_API_KEY})
        price = self._safe_float(payload.get("close") or payload.get("price"))
        if price is None or price <= 0:
            return None
        previous_close = self._safe_float(payload.get("previous_close"))
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=self._safe_float(payload.get("open")),
            high_price=self._safe_float(payload.get("high")),
            low_price=self._safe_float(payload.get("low")),
            previous_close=previous_close,
            volume=self._safe_int(payload.get("volume")),
            market_cap=None,
            change=self._safe_float(payload.get("change")) or 0.0,
            change_percent=self._safe_float(payload.get("percent_change")) or 0.0,
            currency=payload.get("currency", self._default_currency_for_watchlist(watchlist)),
            provider="twelve_data",
        )

    async def _fetch_finnhub_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.FINNHUB_API_KEY:
            return None
        payload = await self._request_json("https://finnhub.io/api/v1/quote", params={"symbol": alias, "token": settings.FINNHUB_API_KEY})
        price = self._safe_float(payload.get("c"))
        previous_close = self._safe_float(payload.get("pc"))
        if price is None or price <= 0:
            return None
        change = price - previous_close if previous_close not in (None, 0) else 0.0
        change_percent = (change / previous_close) * 100 if previous_close not in (None, 0) else 0.0
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=self._safe_float(payload.get("o")),
            high_price=self._safe_float(payload.get("h")),
            low_price=self._safe_float(payload.get("l")),
            previous_close=previous_close,
            volume=0,
            market_cap=None,
            change=change,
            change_percent=change_percent,
            currency=self._default_currency_for_watchlist(watchlist),
            provider="finnhub",
        )

    async def _fetch_fmp_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.FMP_API_KEY:
            return None
        quote_data: dict[str, Any] | None = None
        for endpoint, params in [
            ("https://financialmodelingprep.com/stable/quote", {"symbol": alias, "apikey": settings.FMP_API_KEY}),
            (f"https://financialmodelingprep.com/api/v3/quote-short/{alias}", {"apikey": settings.FMP_API_KEY}),
        ]:
            payload = await self._request_json(endpoint, params=params)
            if isinstance(payload, list) and payload:
                quote_data = payload[0]
                break
            if isinstance(payload, dict) and payload.get("symbol"):
                quote_data = payload
                break
        if quote_data is None:
            return None
        price = self._safe_float(quote_data.get("price"))
        if price is None or price <= 0:
            return None
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=None,
            high_price=None,
            low_price=None,
            previous_close=None,
            volume=self._safe_int(quote_data.get("volume")),
            market_cap=None,
            change=0.0,
            change_percent=0.0,
            currency=self._default_currency_for_watchlist(watchlist),
            provider="financial_modeling_prep",
        )

    async def _fetch_alpha_vantage_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.ALPHA_VANTAGE_KEY:
            return None
        client = AlphaVantageClient()
        try:
            payload = await client.get_quote(alias)
        finally:
            await client.close()
        if not payload:
            return None
        price = self._safe_float(payload.get("05. price"))
        if price is None or price <= 0:
            return None
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=self._safe_float(payload.get("02. open")),
            high_price=self._safe_float(payload.get("03. high")),
            low_price=self._safe_float(payload.get("04. low")),
            previous_close=self._safe_float(payload.get("08. previous close")),
            volume=self._safe_int(payload.get("06. volume")),
            market_cap=None,
            change=self._safe_float(payload.get("09. change")) or 0.0,
            change_percent=self._safe_float(payload.get("10. change percent")) or 0.0,
            currency=self._default_currency_for_watchlist(watchlist),
            provider="alpha_vantage",
        )

    async def _fetch_marketstack_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.MARKETSTACK_API_KEY:
            return None
        payload = await self._request_json(
            "https://api.marketstack.com/v2/eod/latest",
            params={"access_key": settings.MARKETSTACK_API_KEY, "symbols": alias},
        )
        data = payload.get("data", [])
        if not data:
            return None
        quote_data = data[0]
        price = self._safe_float(quote_data.get("close"))
        if price is None or price <= 0:
            return None
        open_price = self._safe_float(quote_data.get("open"))
        previous_close = self._safe_float(quote_data.get("previous_close")) or self._safe_float(quote_data.get("close"))
        change = price - previous_close if previous_close not in (None, 0) else 0.0
        change_percent = (change / previous_close) * 100 if previous_close not in (None, 0) else 0.0
        return NormalizedMarketQuote(
            symbol=watchlist.symbol.upper(),
            alias_used=alias,
            name=watchlist.name,
            market_type=watchlist.market_type,
            exchange=watchlist.exchange,
            price=price,
            open_price=open_price,
            high_price=self._safe_float(quote_data.get("high")),
            low_price=self._safe_float(quote_data.get("low")),
            previous_close=previous_close,
            volume=self._safe_int(quote_data.get("volume")),
            market_cap=None,
            change=change,
            change_percent=change_percent,
            currency=self._default_currency_for_watchlist(watchlist),
            provider="marketstack",
        )

    @staticmethod
    def _quote_provider_name(fetcher: Any) -> str:
        mapping = {
            "_fetch_stockanalysis_quote": "stockanalysis_market",
            "_fetch_dfm_marketwatch_quote": "dfm_marketwatch",
            "_fetch_yahoo_chart_quote": "yahoo_chart",
            "_fetch_twelve_data_quote": "twelve_data",
            "_fetch_finnhub_quote": "finnhub",
            "_fetch_fmp_quote": "financial_modeling_prep",
            "_fetch_alpha_vantage_quote": "alpha_vantage",
            "_fetch_marketstack_quote": "marketstack",
        }
        return mapping.get(fetcher.__name__, fetcher.__name__)

    @staticmethod
    def _merge_market_quotes(primary: NormalizedMarketQuote, validation: NormalizedMarketQuote) -> NormalizedMarketQuote:
        merged_supporting = list(
            dict.fromkeys(
                [
                    *primary.supporting_providers,
                    validation.provider,
                    *validation.supporting_providers,
                ]
            )
        )
        return NormalizedMarketQuote(
            symbol=primary.symbol,
            alias_used=primary.alias_used,
            name=primary.name,
            market_type=primary.market_type,
            exchange=primary.exchange,
            price=primary.price,
            open_price=primary.open_price if primary.open_price is not None else validation.open_price,
            high_price=primary.high_price if primary.high_price is not None else validation.high_price,
            low_price=primary.low_price if primary.low_price is not None else validation.low_price,
            previous_close=primary.previous_close if primary.previous_close is not None else validation.previous_close,
            volume=primary.volume or validation.volume,
            market_cap=primary.market_cap if primary.market_cap is not None else validation.market_cap,
            change=primary.change,
            change_percent=primary.change_percent,
            currency=primary.currency or validation.currency,
            provider=primary.provider,
            supporting_providers=merged_supporting,
        )

    async def _call_quote_provider(
        self,
        provider_name: str,
        fetcher: Any,
        watchlist: WatchlistSymbol,
        alias: str,
    ) -> NormalizedMarketQuote | None:
        async def _wrapped() -> NormalizedMarketQuote | None:
            return await fetcher(watchlist, alias)

        return await provider_health.call_provider(provider_name, _wrapped)

    async def _fetch_fallback_quote_for_symbol(self, watchlist: WatchlistSymbol, aliases: list[str]) -> NormalizedMarketQuote | None:
        fetchers = self._enabled_quote_fetchers(include_yahoo_chart=True)
        for alias in aliases:
            for provider_name, fetcher in fetchers:
                try:
                    quote = await self._call_quote_provider(provider_name, fetcher, watchlist, alias)
                except Exception as exc:
                    logger.debug("Quote provider {} failed for {}: {}", provider_name, alias, str(exc))
                    continue
                if quote is not None:
                    return quote
        return None

    @staticmethod
    def _prefer_regional_quote_source(watchlist: WatchlistSymbol) -> bool:
        return (
            watchlist.market_type == MarketType.STOCK
            and watchlist.exchange in {StockExchange.DFM, StockExchange.ADX}
        )

    async def fetch_market_quotes(self, watchlist_symbols: list[WatchlistSymbol]) -> list[NormalizedMarketQuote]:
        yahoo_eligible_symbols = [item for item in watchlist_symbols if not self._prefer_regional_quote_source(item)]
        yahoo_quotes = await self._fetch_yahoo_quotes(yahoo_eligible_symbols) if self._is_provider_enabled("yahoo_finance") and yahoo_eligible_symbols else []
        quotes_by_symbol = {quote.symbol: quote for quote in yahoo_quotes}
        aliases_by_symbol, _ = self._build_symbol_aliases(watchlist_symbols)

        for item in watchlist_symbols:
            if not self._prefer_regional_quote_source(item):
                continue
            preferred_quote = await self._fetch_fallback_quote_for_symbol(item, aliases_by_symbol[item.symbol.upper()])
            if preferred_quote is None:
                continue
            existing_quote = quotes_by_symbol.get(item.symbol.upper())
            if existing_quote is not None and existing_quote.provider != preferred_quote.provider:
                preferred_quote = self._merge_market_quotes(preferred_quote, existing_quote)
            quotes_by_symbol[item.symbol.upper()] = preferred_quote

        for item in watchlist_symbols:
            if item.symbol.upper() in quotes_by_symbol:
                continue
            quote = await self._fetch_fallback_quote_for_symbol(item, aliases_by_symbol[item.symbol.upper()])
            if quote is not None:
                quotes_by_symbol[item.symbol.upper()] = quote

        validation_fetchers = self._enabled_quote_fetchers(include_yahoo_chart=False)
        if not validation_fetchers:
            return list(quotes_by_symbol.values())

        validation_rotation = datetime.now(timezone.utc).hour % len(validation_fetchers)
        rotated_fetchers = validation_fetchers[validation_rotation:] + validation_fetchers[:validation_rotation]

        for item in self._select_validation_candidates(watchlist_symbols):
            primary_quote = quotes_by_symbol.get(item.symbol.upper())
            if primary_quote is None:
                continue
            attempted_providers = {self._registry_provider_name(primary_quote.provider), *primary_quote.supporting_providers}
            validation_quotes: list[NormalizedMarketQuote] = []
            for provider_name, fetcher in rotated_fetchers[:3]:
                if self._registry_provider_name(provider_name) in attempted_providers:
                    continue
                validation_quote: NormalizedMarketQuote | None = None
                for alias in aliases_by_symbol[item.symbol.upper()]:
                    try:
                        validation_quote = await self._call_quote_provider(provider_name, fetcher, item, alias)
                    except Exception as exc:
                        logger.debug("Validation provider {} failed for {}: {}", provider_name, alias, str(exc))
                        continue
                    if validation_quote is not None:
                        break
                if validation_quote is None:
                    continue
                validation_quotes.append(validation_quote)
                attempted_providers.add(self._registry_provider_name(provider_name))

            if validation_quotes:
                merged_quotes = [primary_quote, *validation_quotes]
                canonical = self._pick_primary_quote(merged_quotes)
                for candidate in merged_quotes:
                    if candidate is canonical:
                        continue
                    canonical = self._merge_market_quotes(canonical, candidate)
                quotes_by_symbol[item.symbol.upper()] = canonical

        return list(quotes_by_symbol.values())

    async def _fetch_massive_forex_rates(self) -> list[NormalizedCurrencyRate]:
        if not settings.MASSIVE_API_KEY:
            return []

        rates: list[NormalizedCurrencyRate] = []
        for from_currency, to_currency in self.CURRENCY_PAIRS:
            try:
                payload = await self._request_json(
                    f"https://api.massive.com/v2/aggs/ticker/C:{from_currency}{to_currency}/prev",
                    params={"adjusted": "true", "apiKey": settings.MASSIVE_API_KEY},
                )
            except Exception as exc:
                logger.debug("Massive forex fetch failed for {}/{}: {}", from_currency, to_currency, str(exc))
                continue

            result = payload.get("results", {})
            if isinstance(result, list):
                result = result[0] if result else {}
            rate = self._safe_float(result.get("c"))
            timestamp = result.get("t")
            if rate is None or rate <= 0 or timestamp is None:
                continue
            rates.append(
                NormalizedCurrencyRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    timestamp=datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc),
                    source="massive",
                )
            )
        return rates

    async def _fetch_exchange_rate_api_rates(self) -> list[NormalizedCurrencyRate]:
        if not settings.EXCHANGERATE_API_KEY:
            return []

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            try:
                payload = await self._request_json(
                    f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGERATE_API_KEY}/pair/{base_currency}/{quote_currency}"
                )
            except Exception as exc:
                logger.debug("ExchangeRate-API fetch failed for {}/{}: {}", base_currency, quote_currency, str(exc))
                continue
            rate = self._safe_float(payload.get("conversion_rate"))
            if rate is None:
                continue
            rates.append(
                NormalizedCurrencyRate(
                    from_currency=base_currency,
                    to_currency=quote_currency,
                    rate=rate,
                    timestamp=self._parse_datetime(payload.get("time_last_update_utc")),
                    source="exchange_rate_api",
                )
            )
        return rates

    async def _fetch_frankfurter_rates(self) -> list[NormalizedCurrencyRate]:
        pairs_by_base: dict[str, set[str]] = {}
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            pairs_by_base.setdefault(base_currency, set()).add(quote_currency)

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currencies in pairs_by_base.items():
            payload: dict[str, Any] | None = None
            try:
                payload = await self._request_json(
                    settings.FRANKFURTER_API_URL,
                    params={"base": base_currency, "symbols": ",".join(sorted(quote_currencies))},
                )
            except Exception:
                payload = None
            if not payload or not payload.get("rates"):
                continue

            timestamp = self._parse_datetime(payload.get("date"))
            for quote_currency, rate in payload.get("rates", {}).items():
                normalized_rate = self._safe_float(rate)
                if normalized_rate is None:
                    continue
                rates.append(
                    NormalizedCurrencyRate(
                        from_currency=base_currency,
                        to_currency=quote_currency,
                        rate=normalized_rate,
                        timestamp=timestamp,
                        source="frankfurter",
                    )
                )
        return rates

    async def _fetch_currencyapi_rates(self) -> list[NormalizedCurrencyRate]:
        if not settings.CURRENCYAPI_KEY:
            return []

        pairs_by_base: dict[str, set[str]] = {}
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            pairs_by_base.setdefault(base_currency, set()).add(quote_currency)

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currencies in pairs_by_base.items():
            try:
                payload = await self._request_json(
                    "https://api.currencyapi.com/v3/latest",
                    params={
                        "apikey": settings.CURRENCYAPI_KEY,
                        "base_currency": base_currency,
                        "currencies": ",".join(sorted(quote_currencies)),
                    },
                )
            except Exception as exc:
                logger.debug("CurrencyAPI fetch failed for {}: {}", base_currency, str(exc))
                continue

            for quote_currency, quote_payload in payload.get("data", {}).items():
                rate = self._safe_float(quote_payload.get("value"))
                if rate is None:
                    continue
                rates.append(
                    NormalizedCurrencyRate(
                        from_currency=base_currency,
                        to_currency=quote_currency,
                        rate=rate,
                        timestamp=datetime.now(timezone.utc),
                        source="currencyapi",
                    )
                )
        return rates

    async def _fetch_fixer_rates(self) -> list[NormalizedCurrencyRate]:
        if not settings.FIXER_API_KEY:
            return []

        try:
            payload = await self._request_json(
                "https://data.fixer.io/api/latest",
                params={"access_key": settings.FIXER_API_KEY},
            )
        except Exception as exc:
            logger.debug("Fixer fetch failed: {}", str(exc))
            return []

        eur_rates = payload.get("rates", {})
        eur_to_aed = self._safe_float(eur_rates.get("AED"))
        if eur_to_aed in (None, 0):
            return []

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            eur_to_base = 1.0 if base_currency == "EUR" else self._safe_float(eur_rates.get(base_currency))
            eur_to_quote = 1.0 if quote_currency == "EUR" else self._safe_float(eur_rates.get(quote_currency))
            if eur_to_base in (None, 0) or eur_to_quote is None:
                continue
            rates.append(
                NormalizedCurrencyRate(
                    from_currency=base_currency,
                    to_currency=quote_currency,
                    rate=eur_to_quote / eur_to_base,
                    timestamp=self._parse_datetime(payload.get("date")),
                    source="fixer",
                )
            )
        return rates

    async def _fetch_currencyfreaks_rates(self) -> list[NormalizedCurrencyRate]:
        if not settings.CURRENCYFREAKS_API_KEY:
            return []

        pairs_by_base: dict[str, set[str]] = {}
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            pairs_by_base.setdefault(base_currency, set()).add(quote_currency)

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currencies in pairs_by_base.items():
            try:
                payload = await self._request_json(
                    "https://api.currencyfreaks.com/v2.0/rates/latest",
                    params={
                        "apikey": settings.CURRENCYFREAKS_API_KEY,
                        "base": base_currency,
                        "symbols": ",".join(sorted(quote_currencies)),
                    },
                )
            except Exception as exc:
                logger.debug("CurrencyFreaks fetch failed for {}: {}", base_currency, str(exc))
                continue

            for quote_currency, quote_value in payload.get("rates", {}).items():
                rate = self._safe_float(quote_value)
                if rate is None:
                    continue
                rates.append(
                    NormalizedCurrencyRate(
                        from_currency=base_currency,
                        to_currency=quote_currency,
                        rate=rate,
                        timestamp=datetime.now(timezone.utc),
                        source="currencyfreaks",
                    )
                )
        return rates

    async def fetch_currency_rates(self) -> list[NormalizedCurrencyRate]:
        provider_plan = [
            ("massive", self._fetch_massive_forex_rates),
            ("frankfurter", self._fetch_frankfurter_rates),
            ("exchange_rate_api", self._fetch_exchange_rate_api_rates),
            ("currencyapi", self._fetch_currencyapi_rates),
            ("currencyfreaks", self._fetch_currencyfreaks_rates),
            ("fixer", self._fetch_fixer_rates),
        ]

        selected_plan: list[tuple[str, Any]] = []
        rotating_plan: list[tuple[str, Any]] = []
        for index, item in enumerate(provider_plan):
            provider_name, _ = item
            if not self._is_provider_enabled(provider_name):
                continue
            if index < 2:
                selected_plan.append(item)
            else:
                rotating_plan.append(item)

        if rotating_plan:
            rotation = datetime.now(timezone.utc).hour % len(rotating_plan)
            rotated = rotating_plan[rotation:] + rotating_plan[:rotation]
            selected_plan.extend(rotated[:2])

        all_rates: list[NormalizedCurrencyRate] = []
        if selected_plan:
            results = await asyncio.gather(
                *(provider_health.call_provider(provider_name, fetcher) for provider_name, fetcher in selected_plan),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, Exception):
                    continue
                all_rates.extend(result)

        pairs_needed = {(base, quote) for base, quote in self.CURRENCY_PAIRS}
        covered_pairs = {(rate.from_currency, rate.to_currency) for rate in all_rates}
        if covered_pairs != pairs_needed:
            remaining_plan = [
                item
                for item in provider_plan
                if self._is_provider_enabled(item[0]) and item not in selected_plan
            ]
            if remaining_plan:
                results = await asyncio.gather(
                    *(provider_health.call_provider(provider_name, fetcher) for provider_name, fetcher in remaining_plan),
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    all_rates.extend(result)

        if all_rates:
            grouped_rates: dict[tuple[str, str], list[NormalizedCurrencyRate]] = {}
            for rate in all_rates:
                grouped_rates.setdefault((rate.from_currency, rate.to_currency), []).append(rate)
            merged_rates = [
                self._merge_currency_rates_for_pair(grouped_rates[pair])
                for pair in sorted(grouped_rates)
                if grouped_rates[pair]
            ]
            if merged_rates:
                return merged_rates

        if not settings.ALPHA_VANTAGE_KEY:
            return []

        client = AlphaVantageClient()
        try:
            fallback_rates: list[NormalizedCurrencyRate] = []
            for from_currency, to_currency in self.CURRENCY_PAIRS:
                payload = await provider_health.call_provider(
                    "alpha_vantage",
                    lambda from_currency=from_currency, to_currency=to_currency: client.get_currency_exchange_rate(from_currency, to_currency),
                )
                rate = self._safe_float(payload.get("5. Exchange Rate"))
                if rate is None:
                    continue
                fallback_rates.append(
                    NormalizedCurrencyRate(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        timestamp=self._parse_datetime(payload.get("6. Last Refreshed")),
                        source="alpha_vantage",
                    )
                )
            return fallback_rates
        finally:
            await client.close()

    async def fetch_market_weather(
        self,
        *,
        location_name: str = "Dubai",
    ) -> NormalizedWeatherSnapshot | None:
        coordinates = self.OPEN_METEO_LOCATIONS.get(location_name, self.OPEN_METEO_LOCATIONS["Dubai"])
        payload = await self._request_json(
            settings.OPEN_METEO_API_URL,
            params={
                "latitude": coordinates[0],
                "longitude": coordinates[1],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
                "timezone": "Asia/Dubai",
            },
        )
        current = payload.get("current", {})
        temperature = self._safe_float(current.get("temperature_2m"))
        if temperature is None:
            return None

        weather_code = self._safe_int(current.get("weather_code")) if current.get("weather_code") is not None else None
        return NormalizedWeatherSnapshot(
            location_name=location_name,
            latitude=float(payload.get("latitude", coordinates[0])),
            longitude=float(payload.get("longitude", coordinates[1])),
            temperature_c=temperature,
            apparent_temperature_c=self._safe_float(current.get("apparent_temperature")),
            humidity_percent=self._safe_int(current.get("relative_humidity_2m")) if current.get("relative_humidity_2m") is not None else None,
            wind_speed_kph=self._safe_float(current.get("wind_speed_10m")),
            weather_code=weather_code,
            weather_summary=self.WEATHER_CODE_SUMMARIES.get(weather_code or -1, "Current conditions"),
            observed_at=self._parse_datetime(current.get("time")),
        )

    async def fetch_world_bank_indicators(self, country: str = "ARE") -> list[NormalizedEconomicIndicator]:
        indicators: list[NormalizedEconomicIndicator] = []
        for indicator_code, indicator_name in self.WORLD_BANK_INDICATORS.items():
            try:
                payload = await self._request_json(
                    f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator_code}",
                    params={"format": "json", "per_page": 5},
                )
            except Exception as exc:
                logger.warning("World Bank fetch failed for {}: {}", indicator_code, str(exc))
                continue

            if not isinstance(payload, list) or len(payload) < 2:
                continue

            for record in payload[1]:
                value = self._safe_float(record.get("value"))
                if value is None:
                    continue
                indicators.append(
                    NormalizedEconomicIndicator(
                        indicator_name=indicator_name,
                        indicator_code=indicator_code,
                        value=value,
                        unit=None,
                        period=str(record.get("date")) if record.get("date") else None,
                        timestamp=datetime.now(timezone.utc),
                        source="World Bank",
                        description=self._clean_text(record.get("indicator", {}).get("value"), 500),
                    )
                )
                break
        return indicators

    async def fetch_fred_indicators(self) -> list[NormalizedEconomicIndicator]:
        if not settings.FRED_API_KEY:
            return []

        indicators: list[NormalizedEconomicIndicator] = []
        for series_id, (indicator_name, country) in self.FRED_INDICATORS.items():
            try:
                payload = await self._request_json(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": series_id,
                        "api_key": settings.FRED_API_KEY,
                        "file_type": "json",
                        "limit": 1,
                        "sort_order": "desc",
                    },
                )
            except Exception as exc:
                logger.warning("FRED fetch failed for {}: {}", series_id, str(exc))
                continue

            observations = payload.get("observations", [])
            if not observations:
                continue
            record = observations[0]
            value = self._safe_float(record.get("value"))
            if value is None:
                continue
            indicators.append(
                NormalizedEconomicIndicator(
                    indicator_name=indicator_name,
                    indicator_code=series_id,
                    value=value,
                    unit=None,
                    period=record.get("date"),
                    timestamp=datetime.now(timezone.utc),
                    source=f"FRED:{country}",
                    description=indicator_name,
                )
            )
        return indicators

    async def fetch_dubai_open_data_metadata(self) -> list[dict[str, Any]]:
        datasets: list[dict[str, Any]] = []
        for dataset_name, dataset in self.DUBAI_OPEN_DATASETS.items():
            entry = {
                "name": dataset_name,
                "url": dataset["url"],
                "description": dataset["description"],
                "accessible": False,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                response = await self.client.get(dataset["url"])
                entry["accessible"] = response.status_code == 200 and "Request Rejected" not in response.text
                entry["status_code"] = response.status_code
            except Exception as exc:
                entry["error"] = str(exc)
            datasets.append(entry)
        return datasets

    async def fetch_reddit_mentions(self, query: str = "Dubai real estate") -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for subreddit in ["dubai", "realestate"]:
            try:
                payload = await self._request_json(
                    f"https://www.reddit.com/r/{subreddit}/search.json",
                    params={"q": query, "restrict_sr": "1", "sort": "new", "t": "month", "limit": 10},
                    headers={"User-Agent": "DUBNEWSAI/1.0"},
                )
            except Exception as exc:
                logger.warning("Reddit fetch failed for r/{}: {}", subreddit, str(exc))
                continue

            for child in payload.get("data", {}).get("children", []):
                data = child.get("data", {})
                title = self._clean_text(data.get("title"), 500)
                if not title or not self._looks_relevant(title, data.get("selftext")):
                    continue
                records.append(
                    {
                        "source": "reddit",
                        "subreddit": subreddit,
                        "title": title,
                        "url": f"https://www.reddit.com{data.get('permalink', '')}",
                        "score": data.get("score", 0),
                        "comments": data.get("num_comments", 0),
                        "published_at": datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc).isoformat(),
                    }
                )
        return records

    async def fetch_twitter_mentions(self, query: str = "Dubai real estate") -> list[dict[str, Any]]:
        if not settings.TWITTER_BEARER_TOKEN:
            return []
        payload = await self._request_json(
            "https://api.twitter.com/2/tweets/search/recent",
            params={"query": query, "max_results": 25, "tweet.fields": "created_at,public_metrics"},
            headers={"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"},
        )
        records: list[dict[str, Any]] = []
        for tweet in payload.get("data", []):
            text = self._clean_text(tweet.get("text"), 1000)
            if not text or not self._looks_relevant(text):
                continue
            records.append(
                {
                    "source": "twitter",
                    "id": tweet.get("id"),
                    "text": text,
                    "published_at": tweet.get("created_at"),
                    "metrics": tweet.get("public_metrics", {}),
                }
            )
        return records

    async def fetch_youtube_mentions(self, query: str = "Dubai real estate") -> list[dict[str, Any]]:
        if not settings.YOUTUBE_API_KEY:
            return []
        payload = await self._request_json(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 10,
                "key": settings.YOUTUBE_API_KEY,
            },
        )
        records: list[dict[str, Any]] = []
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            title = self._clean_text(snippet.get("title"), 500)
            description = self._clean_text(snippet.get("description"), 2000)
            if not title or not self._looks_relevant(title, description):
                continue
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            records.append(
                {
                    "source": "youtube",
                    "title": title,
                    "description": description,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                }
            )
        return records

    async def fetch_trading_economics_indicators(self) -> list[dict[str, Any]]:
        if not settings.TRADING_ECONOMICS_API_KEY:
            return []
        payload = await self._request_json(
            "https://api.tradingeconomics.com/country/united arab emirates",
            params={"c": settings.TRADING_ECONOMICS_API_KEY, "f": "json"},
        )
        if not isinstance(payload, list):
            return []
        records: list[dict[str, Any]] = []
        for item in payload[:25]:
            category = self._clean_text(item.get("Category"), 200)
            latest_value = self._safe_float(item.get("LatestValue"))
            if not category or latest_value is None:
                continue
            records.append(
                {
                    "source": "trading_economics",
                    "category": category,
                    "value": latest_value,
                    "unit": item.get("Unit"),
                    "date": item.get("DateTime"),
                    "ticker": item.get("Ticker"),
                }
            )
        return records
