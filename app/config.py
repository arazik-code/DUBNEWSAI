from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "DUBNEWSAI"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Keep this as a plain string in env vars so platforms like Railway can pass
    # either a single URL or a comma-separated list without JSON encoding.
    CORS_ORIGINS: str = "http://localhost:3000"

    NEWSAPI_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    OPENWEATHER_KEY: str = ""
    RAPID_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    RATE_LIMIT_PER_MINUTE: int = 60

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    FRONTEND_URL: str = "http://localhost:3000"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PREMIUM_MONTHLY_PRICE_ID: str = ""
    STRIPE_PREMIUM_YEARLY_PRICE_ID: str = ""

    BETTERSTACK_SOURCE_TOKEN: str = ""
    BETTERSTACK_HEARTBEAT_CHECK_ID: str = ""

    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]
        return origins or ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
