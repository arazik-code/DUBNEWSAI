from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.news import NewsCategory, NewsSentiment, NewsSource


class NewsArticleCreate(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    description: str | None = None
    content: str | None = None
    url: HttpUrl
    source: NewsSource
    source_name: str | None = Field(default=None, max_length=200)
    author: str | None = Field(default=None, max_length=200)
    category: NewsCategory = NewsCategory.GENERAL
    published_at: datetime
    image_url: HttpUrl | None = None
    video_url: HttpUrl | None = None


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    description: str | None
    content: str | None
    url: str
    source: NewsSource
    source_name: str | None
    author: str | None
    category: NewsCategory
    sentiment: NewsSentiment
    sentiment_score: int
    keywords: list[str] | None
    entities: dict[str, list[str]] | None
    published_at: datetime
    primary_provider: str | None = None
    duplicate_count: int = 1
    quality_score: float = 50.0
    image_url: str | None
    video_url: str | None
    view_count: int
    relevance_score: int
    is_featured: bool
    is_published: bool
    enrichment_status: str | None = None
    enriched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    articles: list[NewsArticleResponse]


class NewsFilterParams(BaseModel):
    category: NewsCategory | None = None
    source: NewsSource | None = None
    sentiment: NewsSentiment | None = None
    search: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
