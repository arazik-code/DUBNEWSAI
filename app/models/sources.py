from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.market_data import MarketData
    from app.models.news import NewsArticle


class DataProvider(BaseModel):
    __tablename__ = "data_providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    rate_limit_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_per_call: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    total_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    circuit_state: Mapped[str] = mapped_column(String(20), default="closed", nullable=False)
    circuit_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    provider_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    fetch_logs: Mapped[list["ProviderFetchLog"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    article_sources: Mapped[list["ArticleSource"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    market_sources: Mapped[list["MarketDataSource"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )


class ProviderFetchLog(BaseModel):
    __tablename__ = "provider_fetch_logs"

    provider_id: Mapped[int] = mapped_column(ForeignKey("data_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    query: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetch_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    items_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    provider: Mapped[DataProvider] = relationship(back_populates="fetch_logs")


class ArticleSource(BaseModel):
    __tablename__ = "article_sources"
    __table_args__ = (UniqueConstraint("article_id", "provider_id", name="uq_article_sources_article_provider"),)

    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("data_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    article: Mapped["NewsArticle"] = relationship(back_populates="sources")
    provider: Mapped[DataProvider] = relationship(back_populates="article_sources")


class MarketDataSource(BaseModel):
    __tablename__ = "market_data_sources"
    __table_args__ = (UniqueConstraint("market_data_id", "provider_id", name="uq_market_data_sources_market_provider"),)

    market_data_id: Mapped[int] = mapped_column(ForeignKey("market_data.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("data_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    market_data: Mapped["MarketData"] = relationship(back_populates="sources")
    provider: Mapped[DataProvider] = relationship(back_populates="market_sources")
