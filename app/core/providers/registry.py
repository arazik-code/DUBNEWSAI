from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class ProviderType(str, Enum):
    NEWS = "news"
    MARKET = "market"
    ECONOMIC = "economic"
    SOCIAL = "social"
    DATASET = "dataset"


class ProviderPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass(slots=True)
class ProviderConfig:
    name: str
    type: ProviderType
    priority: ProviderPriority
    rate_limit: int
    cost_per_call: float
    reliability_score: float
    enabled: bool
    api_key: str = ""
    base_url: str = ""
    timeout: int = 30
    retry_attempts: int = 2
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderRegistry:
    """Central registry for all external data providers."""

    def __init__(self) -> None:
        self.providers: dict[str, ProviderConfig] = {}
        self._initialize_providers()

    def register(self, config: ProviderConfig) -> None:
        self.providers[config.name] = config

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self.providers.get(name)

    def get_providers_by_type(
        self,
        provider_type: ProviderType,
        *,
        enabled_only: bool = True,
    ) -> list[ProviderConfig]:
        providers = [
            provider
            for provider in self.providers.values()
            if provider.type == provider_type and (provider.enabled or not enabled_only)
        ]
        return sorted(
            providers,
            key=lambda provider: (provider.priority.value, -provider.reliability_score, provider.name),
        )

    def get_healthy_providers(
        self,
        provider_type: ProviderType,
        *,
        min_reliability: float = 50.0,
    ) -> list[ProviderConfig]:
        return [
            provider
            for provider in self.get_providers_by_type(provider_type)
            if provider.reliability_score >= min_reliability
        ]

    def _initialize_providers(self) -> None:
        self._register_news_providers()
        self._register_market_providers()
        self._register_economic_providers()
        self._register_social_providers()
        self._register_dataset_providers()

    def _register_news_providers(self) -> None:
        self.register(
            ProviderConfig(
                name="newsapi",
                type=ProviderType.NEWS,
                priority=ProviderPriority.HIGH,
                rate_limit=100,
                cost_per_call=0.0,
                reliability_score=84.0,
                enabled=bool(settings.NEWSAPI_KEY),
                api_key=settings.NEWSAPI_KEY,
                base_url="https://newsapi.org/v2",
            )
        )
        self.register(
            ProviderConfig(
                name="gnews",
                type=ProviderType.NEWS,
                priority=ProviderPriority.HIGH,
                rate_limit=100,
                cost_per_call=0.0,
                reliability_score=82.0,
                enabled=bool(settings.GNEWS_API_KEY),
                api_key=settings.GNEWS_API_KEY,
                base_url="https://gnews.io/api/v4",
            )
        )
        self.register(
            ProviderConfig(
                name="currents",
                type=ProviderType.NEWS,
                priority=ProviderPriority.HIGH,
                rate_limit=600,
                cost_per_call=0.0,
                reliability_score=80.0,
                enabled=bool(settings.CURRENTS_API_KEY),
                api_key=settings.CURRENTS_API_KEY,
                base_url="https://api.currentsapi.services/v1",
            )
        )
        self.register(
            ProviderConfig(
                name="newsdata",
                type=ProviderType.NEWS,
                priority=ProviderPriority.MEDIUM,
                rate_limit=200,
                cost_per_call=0.0,
                reliability_score=76.0,
                enabled=bool(settings.NEWSDATA_API_KEY),
                api_key=settings.NEWSDATA_API_KEY,
                base_url="https://newsdata.io/api/1",
            )
        )
        self.register(
            ProviderConfig(
                name="thenewsapi",
                type=ProviderType.NEWS,
                priority=ProviderPriority.HIGH,
                rate_limit=500,
                cost_per_call=0.0,
                reliability_score=81.0,
                enabled=bool(settings.THENEWSAPI_KEY),
                api_key=settings.THENEWSAPI_KEY,
                base_url="https://api.thenewsapi.com/v1/news",
            )
        )
        self.register(
            ProviderConfig(
                name="mediastack",
                type=ProviderType.NEWS,
                priority=ProviderPriority.MEDIUM,
                rate_limit=500,
                cost_per_call=0.0,
                reliability_score=74.0,
                enabled=bool(settings.MEDIASTACK_API_KEY),
                api_key=settings.MEDIASTACK_API_KEY,
                base_url="http://api.mediastack.com/v1/news",
            )
        )
        self.register(
            ProviderConfig(
                name="newsapi_ai",
                type=ProviderType.NEWS,
                priority=ProviderPriority.MEDIUM,
                rate_limit=500,
                cost_per_call=0.0,
                reliability_score=78.0,
                enabled=bool(settings.NEWSAPI_AI_KEY),
                api_key=settings.NEWSAPI_AI_KEY,
                base_url="https://eventregistry.org/api/v1/article/getArticles",
            )
        )
        self.register(
            ProviderConfig(
                name="bing_news",
                type=ProviderType.NEWS,
                priority=ProviderPriority.MEDIUM,
                rate_limit=1000,
                cost_per_call=0.0,
                reliability_score=79.0,
                enabled=bool(settings.BING_NEWS_API_KEY),
                api_key=settings.BING_NEWS_API_KEY,
                base_url="https://api.bing.microsoft.com/v7.0/news/search",
            )
        )
        self.register(
            ProviderConfig(
                name="contextual_web",
                type=ProviderType.NEWS,
                priority=ProviderPriority.MEDIUM,
                rate_limit=10000,
                cost_per_call=0.0,
                reliability_score=74.0,
                enabled=bool(settings.CONTEXTUAL_WEB_API_KEY or settings.RAPID_API_KEY),
                api_key=settings.CONTEXTUAL_WEB_API_KEY or settings.RAPID_API_KEY,
                base_url="https://real-time-web-search.p.rapidapi.com/search-news",
            )
        )
        self.register(
            ProviderConfig(
                name="rss_feeds",
                type=ProviderType.NEWS,
                priority=ProviderPriority.LOW,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=68.0,
                enabled=True,
                base_url="rss://dubnewsai/news",
            )
        )
        self.register(
            ProviderConfig(
                name="web_scrapers",
                type=ProviderType.NEWS,
                priority=ProviderPriority.LOW,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=64.0,
                enabled=True,
                base_url="scraper://dubnewsai/dubai-property",
            )
        )

    def _register_market_providers(self) -> None:
        self.register(
            ProviderConfig(
                name="yahoo_finance",
                type=ProviderType.MARKET,
                priority=ProviderPriority.CRITICAL,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=91.0,
                enabled=True,
            )
        )
        self.register(
            ProviderConfig(
                name="twelve_data",
                type=ProviderType.MARKET,
                priority=ProviderPriority.HIGH,
                rate_limit=800,
                cost_per_call=0.0,
                reliability_score=78.0,
                enabled=bool(settings.TWELVE_DATA_API_KEY),
                api_key=settings.TWELVE_DATA_API_KEY,
                base_url="https://api.twelvedata.com",
            )
        )
        self.register(
            ProviderConfig(
                name="finnhub",
                type=ProviderType.MARKET,
                priority=ProviderPriority.HIGH,
                rate_limit=3600,
                cost_per_call=0.0,
                reliability_score=72.0,
                enabled=bool(settings.FINNHUB_API_KEY),
                api_key=settings.FINNHUB_API_KEY,
                base_url="https://finnhub.io/api/v1",
            )
        )
        self.register(
            ProviderConfig(
                name="financial_modeling_prep",
                type=ProviderType.MARKET,
                priority=ProviderPriority.MEDIUM,
                rate_limit=250,
                cost_per_call=0.0,
                reliability_score=70.0,
                enabled=bool(settings.FMP_API_KEY),
                api_key=settings.FMP_API_KEY,
                base_url="https://financialmodelingprep.com",
            )
        )
        self.register(
            ProviderConfig(
                name="alpha_vantage",
                type=ProviderType.MARKET,
                priority=ProviderPriority.MEDIUM,
                rate_limit=500,
                cost_per_call=0.0,
                reliability_score=75.0,
                enabled=bool(settings.ALPHA_VANTAGE_KEY),
                api_key=settings.ALPHA_VANTAGE_KEY,
                base_url="https://www.alphavantage.co/query",
            )
        )
        self.register(
            ProviderConfig(
                name="massive",
                type=ProviderType.MARKET,
                priority=ProviderPriority.HIGH,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=79.0,
                enabled=bool(settings.MASSIVE_API_KEY),
                api_key=settings.MASSIVE_API_KEY,
                base_url="https://api.massive.com/v2",
            )
        )
        self.register(
            ProviderConfig(
                name="frankfurter",
                type=ProviderType.MARKET,
                priority=ProviderPriority.CRITICAL,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=93.0,
                enabled=bool(settings.FRANKFURTER_API_URL),
                base_url=settings.FRANKFURTER_API_URL,
            )
        )
        self.register(
            ProviderConfig(
                name="exchange_rate_api",
                type=ProviderType.MARKET,
                priority=ProviderPriority.MEDIUM,
                rate_limit=1500,
                cost_per_call=0.0,
                reliability_score=80.0,
                enabled=bool(settings.EXCHANGERATE_API_KEY),
                api_key=settings.EXCHANGERATE_API_KEY,
                base_url="https://v6.exchangerate-api.com/v6",
            )
        )
        self.register(
            ProviderConfig(
                name="currencyapi",
                type=ProviderType.MARKET,
                priority=ProviderPriority.MEDIUM,
                rate_limit=300,
                cost_per_call=0.0,
                reliability_score=74.0,
                enabled=bool(settings.CURRENCYAPI_KEY),
                api_key=settings.CURRENCYAPI_KEY,
                base_url="https://api.currencyapi.com/v3/latest",
            )
        )
        self.register(
            ProviderConfig(
                name="currencyfreaks",
                type=ProviderType.MARKET,
                priority=ProviderPriority.LOW,
                rate_limit=1000,
                cost_per_call=0.0,
                reliability_score=65.0,
                enabled=bool(settings.CURRENCYFREAKS_API_KEY),
                api_key=settings.CURRENCYFREAKS_API_KEY,
                base_url="https://api.currencyfreaks.com/v2.0/rates/latest",
            )
        )
        self.register(
            ProviderConfig(
                name="fixer",
                type=ProviderType.MARKET,
                priority=ProviderPriority.LOW,
                rate_limit=100,
                cost_per_call=0.0,
                reliability_score=72.0,
                enabled=bool(settings.FIXER_API_KEY),
                api_key=settings.FIXER_API_KEY,
                base_url="https://data.fixer.io/api/latest",
            )
        )
        self.register(
            ProviderConfig(
                name="marketstack",
                type=ProviderType.MARKET,
                priority=ProviderPriority.LOW,
                rate_limit=1000,
                cost_per_call=0.0,
                reliability_score=67.0,
                enabled=bool(settings.MARKETSTACK_API_KEY),
                api_key=settings.MARKETSTACK_API_KEY,
                base_url="https://api.marketstack.com/v1",
            )
        )

    def _register_economic_providers(self) -> None:
        self.register(
            ProviderConfig(
                name="world_bank",
                type=ProviderType.ECONOMIC,
                priority=ProviderPriority.HIGH,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=90.0,
                enabled=True,
                base_url="https://api.worldbank.org/v2",
            )
        )
        self.register(
            ProviderConfig(
                name="fred",
                type=ProviderType.ECONOMIC,
                priority=ProviderPriority.HIGH,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=88.0,
                enabled=bool(settings.FRED_API_KEY),
                api_key=settings.FRED_API_KEY,
                base_url="https://api.stlouisfed.org/fred",
            )
        )
        self.register(
            ProviderConfig(
                name="trading_economics",
                type=ProviderType.ECONOMIC,
                priority=ProviderPriority.MEDIUM,
                rate_limit=1000,
                cost_per_call=0.0,
                reliability_score=73.0,
                enabled=bool(settings.TRADING_ECONOMICS_API_KEY),
                api_key=settings.TRADING_ECONOMICS_API_KEY,
                base_url="https://api.tradingeconomics.com",
            )
        )

    def _register_social_providers(self) -> None:
        self.register(
            ProviderConfig(
                name="twitter",
                type=ProviderType.SOCIAL,
                priority=ProviderPriority.MEDIUM,
                rate_limit=500000,
                cost_per_call=0.0,
                reliability_score=78.0,
                enabled=bool(settings.TWITTER_BEARER_TOKEN),
                api_key=settings.TWITTER_BEARER_TOKEN,
                base_url="https://api.twitter.com/2",
            )
        )
        self.register(
            ProviderConfig(
                name="youtube",
                type=ProviderType.SOCIAL,
                priority=ProviderPriority.MEDIUM,
                rate_limit=10000,
                cost_per_call=0.0,
                reliability_score=77.0,
                enabled=bool(settings.YOUTUBE_API_KEY),
                api_key=settings.YOUTUBE_API_KEY,
                base_url="https://www.googleapis.com/youtube/v3",
            )
        )
        self.register(
            ProviderConfig(
                name="reddit",
                type=ProviderType.SOCIAL,
                priority=ProviderPriority.LOW,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=70.0,
                enabled=True,
                base_url="https://www.reddit.com",
            )
        )

    def _register_dataset_providers(self) -> None:
        self.register(
            ProviderConfig(
                name="dubai_pulse",
                type=ProviderType.DATASET,
                priority=ProviderPriority.HIGH,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=86.0,
                enabled=True,
                base_url="https://www.dubaipulse.gov.ae",
            )
        )
        self.register(
            ProviderConfig(
                name="open_meteo",
                type=ProviderType.DATASET,
                priority=ProviderPriority.HIGH,
                rate_limit=999999,
                cost_per_call=0.0,
                reliability_score=94.0,
                enabled=True,
                base_url=settings.OPEN_METEO_API_URL,
            )
        )


provider_registry = ProviderRegistry()
