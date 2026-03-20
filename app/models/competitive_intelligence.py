from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class Competitor(BaseModel):
    __tablename__ = "competitors"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    official_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ticker_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_annual: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_share_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitive_strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_analyzed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    products: Mapped[list["CompetitorProduct"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")
    news_mentions: Mapped[list["CompetitorNewsMention"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")
    price_changes: Mapped[list["CompetitorPriceChange"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")
    swot_analyses: Mapped[list["CompetitorSWOT"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")
    benchmarks: Mapped[list["CompetitiveBenchmark"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")


class CompetitorProduct(BaseModel):
    __tablename__ = "competitor_products"

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pricing_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    key_features: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    unique_selling_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    launch_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    market_reception: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="products")


class CompetitorNewsMention(BaseModel):
    __tablename__ = "competitor_news_mentions"

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    article_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    article_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    mention_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    entities_mentioned: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="news_mentions")


class CompetitorPriceChange(BaseModel):
    __tablename__ = "competitor_price_changes"

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_change_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="price_changes")


class CompetitorSWOT(BaseModel):
    __tablename__ = "competitor_swot_analyses"

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    strengths: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    opportunities: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    threats: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    analysis_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    competitive_position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    threat_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="swot_analyses")


class CompetitiveBenchmark(BaseModel):
    __tablename__ = "competitive_benchmarks"

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    competitor_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    our_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    industry_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_vs_competitor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gap_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    data_source: Mapped[str | None] = mapped_column(String(200), nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="benchmarks")


class MarketIntelligenceReport(BaseModel):
    __tablename__ = "market_intelligence_reports"

    report_title: Mapped[str] = mapped_column(String(300), nullable=False)
    report_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    market_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_trends: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    top_players: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    market_concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    reporting_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporting_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
