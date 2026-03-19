from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, enum_kwargs

if TYPE_CHECKING:
    from app.models.sources import ArticleSource


class NewsCategory(str, Enum):
    REAL_ESTATE = "real_estate"
    MARKET = "market"
    ECONOMY = "economy"
    REGULATION = "regulation"
    DEVELOPMENT = "development"
    INFRASTRUCTURE = "infrastructure"
    GENERAL = "general"


class NewsSource(str, Enum):
    NEWSAPI = "newsapi"
    RSS_GULF_NEWS = "rss_gulf_news"
    RSS_THE_NATIONAL = "rss_the_national"
    RSS_KHALEEJ_TIMES = "rss_khaleej_times"
    RSS_ARABIAN_BUSINESS = "rss_arabian_business"
    RAPID_API = "rapid_api"
    TWITTER = "twitter"
    MANUAL = "manual"


class NewsSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# Backward-compatible alias for earlier migrations that import the old enum name.
SentimentLabel = NewsSentiment


news_article_tags = Table(
    "news_article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("news_tags.id", ondelete="CASCADE"), primary_key=True),
)


class NewsArticle(BaseModel):
    __tablename__ = "news_articles"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    source: Mapped[NewsSource] = mapped_column(
        SqlEnum(NewsSource, name="news_source", **enum_kwargs(NewsSource)),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)

    category: Mapped[NewsCategory] = mapped_column(
        SqlEnum(NewsCategory, name="news_category", **enum_kwargs(NewsCategory)),
        default=NewsCategory.GENERAL,
        nullable=False,
        index=True,
    )
    sentiment: Mapped[NewsSentiment] = mapped_column(
        SqlEnum(NewsSentiment, name="news_sentiment", **enum_kwargs(NewsSentiment)),
        default=NewsSentiment.NEUTRAL,
        nullable=False,
        index=True,
    )
    sentiment_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, nullable=True)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    primary_provider: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    enrichment_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    tags: Mapped[list["NewsTag"]] = relationship(
        secondary=news_article_tags,
        back_populates="articles",
    )
    sources: Mapped[list["ArticleSource"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_published_category", "published_at", "category"),
        Index("idx_source_published", "source", "published_at"),
    )


class NewsTag(BaseModel):
    __tablename__ = "news_tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    articles: Mapped[list[NewsArticle]] = relationship(
        secondary=news_article_tags,
        back_populates="tags",
    )
