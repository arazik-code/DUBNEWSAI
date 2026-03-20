from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import check_rate_limit
from app.core.exceptions import ConflictError
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.news import NewsCategory, NewsSentiment, NewsSource
from app.models.user import User
from app.schemas.news import NewsArticleCreate, NewsArticleResponse, NewsFilterParams, NewsListResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/", response_model=NewsListResponse)
async def list_news(
    request: Request,
    category: NewsCategory | None = None,
    source: NewsSource | None = None,
    sentiment: NewsSentiment | None = None,
    search: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_rate_limit),
) -> NewsListResponse:
    """Get paginated news articles.

    **Public Access:** Yes (with rate limiting)
    **Premium Benefits:** Higher rate limits
    """
    del request, current_user  # available for future personalisation
    filters = NewsFilterParams(
        category=category,
        source=source,
        sentiment=sentiment,
        search=search,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return await NewsService.get_articles(db, filters)


@router.get("/featured/top", response_model=list[NewsArticleResponse])
async def get_featured_articles(
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_rate_limit),
) -> list[NewsArticleResponse]:
    """Get featured articles.

    **Public Access:** Yes
    """
    del current_user
    articles = await NewsService.get_featured_articles(db, limit=limit)
    return [NewsArticleResponse.model_validate(article) for article in articles]


@router.get("/trending/today", response_model=list[NewsArticleResponse])
async def get_trending_articles(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_rate_limit),
) -> list[NewsArticleResponse]:
    """Get trending articles from the last 24 hours.

    **Public Access:** Yes
    """
    del current_user
    articles = await NewsService.get_trending_articles(db, limit=limit)
    return [NewsArticleResponse.model_validate(article) for article in articles]


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_news(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_rate_limit),
) -> NewsArticleResponse:
    """Get a single article by ID.

    **Public Access:** Yes
    """
    del current_user
    news_item = await NewsService.get_article_by_id(db, article_id)
    if isinstance(news_item, dict):
        description, content = NewsService._normalize_article_text(
            news_item.get("description"),
            news_item.get("content"),
        )
        news_item["description"] = description
        news_item["content"] = content
    return NewsArticleResponse.model_validate(news_item)


@router.post("/", response_model=NewsArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    request: Request,
    payload: NewsArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit),
) -> NewsArticleResponse:
    """Create a new article. **Requires authentication.**"""
    del request
    article_data = payload.model_copy(
        update={
            "source": payload.source,
            "author": payload.author or current_user.full_name or current_user.email,
        }
    )
    news_item = await NewsService.create_article(db, article_data)
    if news_item is None:
        raise ConflictError("Article already exists")
    return NewsArticleResponse.model_validate(news_item)
