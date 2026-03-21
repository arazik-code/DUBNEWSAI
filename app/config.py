from functools import lru_cache
import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "DUBNEWSAI"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    ENABLE_EMBEDDED_SYNC: bool | None = None
    EMBEDDED_NEWS_SYNC_MINUTES: int = 2
    EMBEDDED_MARKET_SYNC_MINUTES: int = 15
    ENABLE_PREDICTIONS: bool = True
    PREDICTION_CACHE_HOURS: int = 24
    EXECUTIVE_FEATURES: bool = True
    PUBLIC_API_ENABLED: bool = True
    DEFAULT_API_RATE_LIMIT: int = 100
    MAX_TEAM_MEMBERS: int = 10
    ENABLE_TEAM_FEATURES: bool = True

    DATABASE_URL: str
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Keep this as a plain string in env vars so platforms like Railway can pass
    # either a single URL or a comma-separated list without JSON encoding.
    CORS_ORIGINS: str = "http://localhost:3000 https://dubnewsai.vercel.app"

    NEWSAPI_KEY: str = ""
    GNEWS_API_KEY: str = ""
    CURRENTS_API_KEY: str = ""
    NEWSDATA_API_KEY: str = ""
    THENEWSAPI_KEY: str = ""
    MEDIASTACK_API_KEY: str = ""
    NEWSAPI_AI_KEY: str = ""
    CONTEXTUAL_WEB_API_KEY: str = ""
    BING_NEWS_API_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    TWELVE_DATA_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    FMP_API_KEY: str = ""
    MASSIVE_API_KEY: str = ""
    MARKETSTACK_API_KEY: str = ""
    FRED_API_KEY: str = ""
    OPENWEATHER_KEY: str = ""
    RAPID_API_KEY: str = ""
    EXCHANGERATE_API_KEY: str = ""
    CURRENCYAPI_KEY: str = ""
    CURRENCYFREAKS_API_KEY: str = ""
    FIXER_API_KEY: str = ""
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    GOOGLE_PLACES_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    YOUTUBE_API_KEY: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    TRADING_ECONOMICS_API_KEY: str = ""
    FRANKFURTER_API_URL: str = "https://api.frankfurter.app/latest"

    RATE_LIMIT_PER_MINUTE: int = 60

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    FRONTEND_URL: str = "https://dubnewsai.vercel.app"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PREMIUM_MONTHLY_PRICE_ID: str = ""
    STRIPE_PREMIUM_YEARLY_PRICE_ID: str = ""

    BETTERSTACK_SOURCE_TOKEN: str = ""
    BETTERSTACK_HEARTBEAT_CHECK_ID: str = ""

    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    NEWS_LOOKBACK_DAYS: int = 7
    NEWS_PROVIDER_ARTICLE_LIMIT: int = 10
    ARTICLE_MIN_CONTENT_LENGTH: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            if "pooler.supabase.com:6543/" in value:
                value = value.replace("pooler.supabase.com:6543/", "pooler.supabase.com:5432/", 1)
            if value.startswith("postgresql+asyncpg://") or value.startswith("sqlite+aiosqlite://"):
                return value
            if value.startswith("postgresql://"):
                return value.replace("postgresql://", "postgresql+asyncpg://", 1)
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @staticmethod
    def _normalize_origin(origin: str) -> str:
        return origin.strip().strip("\"'").rstrip("/")

    @property
    def cors_origins_list(self) -> list[str]:
        raw_origins = re.split(r"[\s,]+", self.CORS_ORIGINS.strip())
        origins: list[str] = []
        for item in raw_origins:
            normalized = self._normalize_origin(item)
            if normalized and normalized not in origins:
                origins.append(normalized)
        frontend_origin = self._normalize_origin(self.FRONTEND_URL)
        if frontend_origin and frontend_origin not in origins:
            origins.append(frontend_origin)
        return origins or ["http://localhost:3000"]

    @property
    def embedded_sync_enabled(self) -> bool:
        if self.ENABLE_EMBEDDED_SYNC is not None:
            return self.ENABLE_EMBEDDED_SYNC
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
