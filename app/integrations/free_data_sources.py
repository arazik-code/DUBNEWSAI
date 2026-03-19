from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
import httpx
import yfinance as yf
from dateutil import parser as date_parser
from loguru import logger

from app.config import get_settings
from app.integrations.alpha_vantage_client import AlphaVantageClient
from app.integrations.newsapi_client import NewsAPIClient
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


@dataclass
class NormalizedCurrencyRate:
    from_currency: str
    to_currency: str
    rate: float
    timestamp: datetime


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
    }

    UAE_SYMBOL_ALIASES: dict[str, list[str]] = {
        "EMAAR": ["EMAAR.DU", "EMAARDEV.AE", "EMAAR.AE"],
        "DAMAC": ["DAMAC.DU", "DAMAC.AE"],
        "DEYAAR": ["DEYAAR.DU", "DEYAAR.AE"],
        "ALDAR": ["ALDAR.AD", "ALDAR.AE"],
        "AMLAK": ["AMLAK.DU", "AMLAK.AE"],
        "UPP": ["UPP.DU", "UNIONPRO.AE", "UPP.AE"],
        "ESHRAQ": ["ESHRAQ.AD", "ESHRAQ.AE"],
        "RAKPROP": ["RAKPROP.AE", "RAKPROP.AD"],
        "^DFM": ["DFMGI.AE", "^DFMGI"],
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

    DUBAI_OPEN_DATASETS: dict[str, dict[str, str]] = {
        "real_estate_transactions": {"url": "https://www.dubaipulse.gov.ae/data/dld-transactions/", "description": "Dubai Land Department transactions dataset landing page"},
        "property_price_index": {"url": "https://www.dubaipulse.gov.ae/data/reidin-property-price/", "description": "Dubai property price index dataset landing page"},
        "building_permits": {"url": "https://www.dubaipulse.gov.ae/data/dm-building-permits/", "description": "Dubai Municipality building permits dataset landing page"},
        "tourism_stats": {"url": "https://www.dubaipulse.gov.ae/data/dtcm-tourism/", "description": "Tourism statistics impacting rental demand"},
    }

    LOCATION_TERMS = ("dubai", "uae", "abu dhabi", "emirates", "dfm", "adx")
    PROPERTY_TERMS = ("property", "real estate", "housing", "villa", "apartment", "rental", "rent", "mortgage", "developer", "off-plan", "residential", "commercial", "construction")

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "DUBNEWSAI/1.0 (+https://dubnewsai.com; Dubai real estate intelligence platform)"},
        )

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
            return float(str(value).replace("%", "").replace(",", ""))
        except Exception:
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            if value in (None, "", "None"):
                return 0
            return int(float(value))
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

    async def _fetch_newsapi(self) -> list[NormalizedNewsRecord]:
        if not settings.NEWSAPI_KEY:
            return []
        client = NewsAPIClient()
        try:
            articles = await client.fetch_dubai_real_estate_news(
                days_back=settings.NEWS_LOOKBACK_DAYS,
                page_size=min(25, settings.NEWS_PROVIDER_ARTICLE_LIMIT * 2),
            )
        finally:
            await client.close()

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
                    source=NewsSource.NEWSAPI,
                    source_name=article.get("source", {}).get("name") or "NewsAPI",
                    author=self._clean_text(article.get("author"), 200),
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("publishedAt")),
                    image_url=self._normalize_url(article.get("urlToImage")),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_gnews(self) -> list[NormalizedNewsRecord]:
        if not settings.GNEWS_API_KEY:
            return []
        payload = await self._request_json(
            "https://gnews.io/api/v4/search",
            params={
                "q": 'Dubai "real estate" OR Dubai property OR Dubai rental',
                "lang": "en",
                "country": "ae",
                "max": settings.NEWS_PROVIDER_ARTICLE_LIMIT,
                "from": (datetime.now(timezone.utc) - timedelta(days=settings.NEWS_LOOKBACK_DAYS)).date().isoformat(),
                "token": settings.GNEWS_API_KEY,
            },
        )
        records: list[NormalizedNewsRecord] = []
        for article in payload.get("articles", []):
            url = self._normalize_url(article.get("url"))
            if not url:
                continue
            records.append(
                NormalizedNewsRecord(
                    title=self._clean_text(article.get("title"), 500) or "Untitled",
                    description=self._clean_text(article.get("description"), 5000),
                    content=self._clean_text(article.get("content"), 50000),
                    url=url,
                    source=NewsSource.RAPID_API,
                    source_name="GNews",
                    author=self._clean_text(article.get("source", {}).get("name") or article.get("author"), 200),
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("publishedAt")),
                    image_url=self._normalize_url(article.get("image")),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_currents(self) -> list[NormalizedNewsRecord]:
        if not settings.CURRENTS_API_KEY:
            return []
        payload = await self._request_json(
            "https://api.currentsapi.services/v1/search",
            params={"keywords": "Dubai real estate", "language": "en", "apiKey": settings.CURRENTS_API_KEY},
        )
        records: list[NormalizedNewsRecord] = []
        for article in payload.get("news", [])[: settings.NEWS_PROVIDER_ARTICLE_LIMIT]:
            url = self._normalize_url(article.get("url"))
            if not url:
                continue
            records.append(
                NormalizedNewsRecord(
                    title=self._clean_text(article.get("title"), 500) or "Untitled",
                    description=self._clean_text(article.get("description"), 5000),
                    content=self._clean_text(article.get("description"), 50000),
                    url=url,
                    source=NewsSource.RAPID_API,
                    source_name="Currents",
                    author=self._clean_text(article.get("author"), 200),
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("published")),
                    image_url=self._normalize_url(article.get("image")),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_newsdata(self) -> list[NormalizedNewsRecord]:
        if not settings.NEWDATA_API_KEY:
            return []
        payload = await self._request_json(
            "https://newsdata.io/api/1/news",
            params={"apikey": settings.NEWDATA_API_KEY, "q": "Dubai real estate OR Dubai property", "language": "en", "country": "ae"},
        )
        records: list[NormalizedNewsRecord] = []
        for article in payload.get("results", [])[: settings.NEWS_PROVIDER_ARTICLE_LIMIT]:
            url = self._normalize_url(article.get("link"))
            if not url:
                continue
            creator = article.get("creator")
            if isinstance(creator, list):
                creator = creator[0] if creator else None
            records.append(
                NormalizedNewsRecord(
                    title=self._clean_text(article.get("title"), 500) or "Untitled",
                    description=self._clean_text(article.get("description"), 5000),
                    content=self._clean_text(article.get("content"), 50000),
                    url=url,
                    source=NewsSource.RAPID_API,
                    source_name="NewsData.io",
                    author=self._clean_text(creator, 200),
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("pubDate")),
                    image_url=self._normalize_url(article.get("image_url")),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_contextual_web(self) -> list[NormalizedNewsRecord]:
        if not settings.CONTEXTUAL_WEB_API_KEY:
            return []
        payload = await self._request_json(
            "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI",
            params={
                "q": "Dubai real estate",
                "pageNumber": 1,
                "pageSize": settings.NEWS_PROVIDER_ARTICLE_LIMIT,
                "autoCorrect": True,
                "withThumbnails": True,
                "fromPublishedDate": (datetime.now(timezone.utc) - timedelta(days=settings.NEWS_LOOKBACK_DAYS)).isoformat(),
            },
            headers={
                "X-RapidAPI-Key": settings.CONTEXTUAL_WEB_API_KEY,
                "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
            },
        )
        records: list[NormalizedNewsRecord] = []
        for article in payload.get("value", []):
            url = self._normalize_url(article.get("url"))
            if not url:
                continue
            image = article.get("image")
            records.append(
                NormalizedNewsRecord(
                    title=self._clean_text(article.get("title"), 500) or "Untitled",
                    description=self._clean_text(article.get("description"), 5000),
                    content=self._clean_text(article.get("body"), 50000),
                    url=url,
                    source=NewsSource.RAPID_API,
                    source_name="Contextual Web Search",
                    author=None,
                    category=self._category_from_text(article.get("title", ""), article.get("description")),
                    published_at=self._parse_datetime(article.get("datePublished")),
                    image_url=self._normalize_url(image.get("url")) if isinstance(image, dict) else None,
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def _fetch_single_rss_feed(self, feed_name: str, feed_url: str, source: NewsSource, source_name: str) -> list[NormalizedNewsRecord]:
        try:
            response = await self.client.get(feed_url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            records: list[NormalizedNewsRecord] = []
            for entry in feed.entries[: settings.NEWS_PROVIDER_ARTICLE_LIMIT]:
                url = self._normalize_url(entry.get("link"))
                if not url:
                    continue
                summary = self._clean_text(entry.get("summary", entry.get("description")), 5000)
                title = self._clean_text(entry.get("title"), 500) or "Untitled"
                image_url = None
                media_content = entry.get("media_content")
                if media_content:
                    image_url = self._normalize_url(media_content[0].get("url"))
                records.append(
                    NormalizedNewsRecord(
                        title=title,
                        description=summary,
                        content=summary,
                        url=url,
                        source=source,
                        source_name=source_name,
                        author=self._clean_text(entry.get("author"), 200),
                        category=self._category_from_text(title, summary),
                        published_at=self._parse_datetime(entry.get("published", entry.get("updated"))),
                        image_url=image_url,
                    )
                )
            return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]
        except Exception as exc:
            logger.warning("RSS source {} unavailable: {}", feed_name, str(exc))
            return []

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
                    author=None,
                    category=self._category_from_text(insight.title, insight.excerpt),
                    published_at=insight.published_at,
                    image_url=self._normalize_url(insight.image_url),
                )
            )
        return [record for record in records if self._looks_relevant(record.title, record.description, record.content)]

    async def fetch_news_articles(self, *, include_api: bool = True, include_rss: bool = True, include_scraped: bool = True) -> list[NewsArticleCreate]:
        jobs: list[Any] = []
        if include_api:
            jobs.extend([self._fetch_newsapi(), self._fetch_gnews(), self._fetch_currents(), self._fetch_newsdata(), self._fetch_contextual_web()])
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
            ordered_aliases = [item.symbol.upper(), *aliases]
            deduped = list(dict.fromkeys(alias.upper() for alias in ordered_aliases))
            aliases_by_symbol[item.symbol.upper()] = deduped
            for alias in deduped:
                if alias not in all_aliases:
                    all_aliases.append(alias)
        return aliases_by_symbol, all_aliases

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
        )

    async def _fetch_yahoo_quotes(self, watchlist_symbols: list[WatchlistSymbol]) -> list[NormalizedMarketQuote]:
        if not watchlist_symbols:
            return []
        aliases_by_symbol, all_aliases = self._build_symbol_aliases(watchlist_symbols)
        try:
            history = await self._download_yahoo_history(all_aliases)
        except Exception as exc:
            logger.warning("Yahoo Finance batch download failed: {}", str(exc))
            return []

        quotes: list[NormalizedMarketQuote] = []
        for item in watchlist_symbols:
            for alias in aliases_by_symbol[item.symbol.upper()]:
                frame = self._extract_yahoo_frame(history, alias, len(all_aliases))
                quote = self._build_quote_from_history(item, alias, frame)
                if quote is not None:
                    quotes.append(quote)
                    break
        return quotes

    async def _fetch_twelve_data_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.TWELVE_DATA_API_KEY:
            return None
        payload = await self._request_json("https://api.twelvedata.com/quote", params={"symbol": alias, "apikey": settings.TWELVE_DATA_API_KEY})
        price = self._safe_float(payload.get("close") or payload.get("price"))
        if price is None:
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
            currency=payload.get("currency", "AED"),
        )

    async def _fetch_finnhub_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.FINNHUB_API_KEY:
            return None
        payload = await self._request_json("https://finnhub.io/api/v1/quote", params={"symbol": alias, "token": settings.FINNHUB_API_KEY})
        price = self._safe_float(payload.get("c"))
        previous_close = self._safe_float(payload.get("pc"))
        if price is None:
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
        )

    async def _fetch_fmp_quote(self, watchlist: WatchlistSymbol, alias: str) -> NormalizedMarketQuote | None:
        if not settings.FMP_API_KEY:
            return None
        payload = await self._request_json(f"https://financialmodelingprep.com/api/v3/quote-short/{alias}", params={"apikey": settings.FMP_API_KEY})
        if not isinstance(payload, list) or not payload:
            return None
        quote_data = payload[0]
        price = self._safe_float(quote_data.get("price"))
        if price is None:
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
        if price is None:
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
        )

    async def _fetch_fallback_quote_for_symbol(self, watchlist: WatchlistSymbol, aliases: list[str]) -> NormalizedMarketQuote | None:
        fetchers = [self._fetch_twelve_data_quote, self._fetch_finnhub_quote, self._fetch_fmp_quote, self._fetch_alpha_vantage_quote]
        for alias in aliases:
            for fetcher in fetchers:
                try:
                    quote = await fetcher(watchlist, alias)
                except Exception as exc:
                    logger.debug("Quote provider {} failed for {}: {}", fetcher.__name__, alias, str(exc))
                    continue
                if quote is not None:
                    return quote
        return None

    async def fetch_market_quotes(self, watchlist_symbols: list[WatchlistSymbol]) -> list[NormalizedMarketQuote]:
        yahoo_quotes = await self._fetch_yahoo_quotes(watchlist_symbols)
        quotes_by_symbol = {quote.symbol: quote for quote in yahoo_quotes}
        aliases_by_symbol, _ = self._build_symbol_aliases(watchlist_symbols)

        for item in watchlist_symbols:
            if item.symbol.upper() in quotes_by_symbol:
                continue
            quote = await self._fetch_fallback_quote_for_symbol(item, aliases_by_symbol[item.symbol.upper()])
            if quote is not None:
                quotes_by_symbol[item.symbol.upper()] = quote

        return list(quotes_by_symbol.values())

    async def fetch_currency_rates(self) -> list[NormalizedCurrencyRate]:
        pairs_by_base: dict[str, set[str]] = {}
        for base_currency, quote_currency in self.CURRENCY_PAIRS:
            pairs_by_base.setdefault(base_currency, set()).add(quote_currency)

        rates: list[NormalizedCurrencyRate] = []
        for base_currency, quote_currencies in pairs_by_base.items():
            payload: dict[str, Any] | None = None
            for endpoint, params in [
                ("https://api.frankfurter.app/latest", {"base": base_currency, "symbols": ",".join(sorted(quote_currencies))}),
                ("https://api.frankfurter.dev/latest", {"base": base_currency, "symbols": ",".join(sorted(quote_currencies))}),
                ("https://api.frankfurter.dev/v1/latest", {"base": base_currency, "symbols": ",".join(sorted(quote_currencies))}),
            ]:
                try:
                    payload = await self._request_json(endpoint, params=params)
                    if payload.get("rates"):
                        break
                except Exception:
                    payload = None
            if not payload or not payload.get("rates"):
                logger.warning("Frankfurter unavailable for base {}", base_currency)
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
                    )
                )

        if rates:
            return rates

        if not settings.ALPHA_VANTAGE_KEY:
            return []

        client = AlphaVantageClient()
        try:
            fallback_rates: list[NormalizedCurrencyRate] = []
            for from_currency, to_currency in self.CURRENCY_PAIRS:
                payload = await client.get_currency_exchange_rate(from_currency, to_currency)
                rate = self._safe_float(payload.get("5. Exchange Rate"))
                if rate is None:
                    continue
                fallback_rates.append(
                    NormalizedCurrencyRate(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        timestamp=self._parse_datetime(payload.get("6. Last Refreshed")),
                    )
                )
            return fallback_rates
        finally:
            await client.close()

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
