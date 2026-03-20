from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.news import NewsCategory
from app.models.user import User
from app.schemas.news import NewsArticleResponse
from app.services.ai_service import AIService
from app.services.news_service import NewsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrendResponse(BaseModel):
    keyword: str
    count: int
    trend_score: int


class SentimentDistribution(BaseModel):
    positive: int
    neutral: int
    negative: int
    total: int
    positive_percent: float
    neutral_percent: float
    negative_percent: float


class AnalyticsOverviewResponse(BaseModel):
    mood: dict
    sentiment_distribution: SentimentDistribution
    trends: list[TrendResponse]
    category_distribution: list[dict]
    sentiment_timeline: list[dict]
    provider_distribution: list[dict]


@router.get("/trends", response_model=list[TrendResponse])
async def get_trending_topics(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[TrendResponse]:
    """Get trending topics.

    **Public Access:** Yes
    """
    del current_user
    return await AIService.detect_trends(db, days=days)


@router.get("/sentiment-distribution", response_model=SentimentDistribution)
async def get_sentiment_distribution(
    category: NewsCategory | None = None,
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> SentimentDistribution:
    """Get sentiment distribution.

    **Public Access:** Yes
    """
    del current_user
    distribution = await AIService.get_sentiment_distribution(db, category, days)
    return SentimentDistribution.model_validate(distribution)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> AnalyticsOverviewResponse:
    del current_user
    sentiment_distribution = await AIService.get_sentiment_distribution(db, days=days)
    trends = await AIService.detect_trends(db, days=days)
    category_distribution = await AIService.get_category_distribution(db, days=days)
    sentiment_timeline = await AIService.get_sentiment_timeline(db, days=days)
    provider_distribution = await AIService.get_provider_distribution(db, days=days)
    mood = await AIService.get_market_mood(db, days=days)
    return AnalyticsOverviewResponse(
        mood=mood,
        sentiment_distribution=SentimentDistribution.model_validate(sentiment_distribution),
        trends=[TrendResponse.model_validate(item) for item in trends],
        category_distribution=category_distribution,
        sentiment_timeline=sentiment_timeline,
        provider_distribution=provider_distribution,
    )


@router.get("/recommendations", response_model=list[NewsArticleResponse])
async def get_personalized_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[NewsArticleResponse]:
    """Get personalised recommendations. **Requires authentication.**"""
    del current_user
    articles = await AIService.get_recommendations(db, limit=limit)
    return [NewsArticleResponse.model_validate(article) for article in articles]


@router.post("/analyze-article/{article_id}")
async def trigger_article_analysis(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict[str, object]:
    """Trigger on-demand AI analysis for an article. **Requires authentication.**"""
    del current_user
    article = await NewsService.analyze_and_update_article(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "message": "Analysis complete",
        "sentiment": article.sentiment.value,
        "sentiment_score": article.sentiment_score,
        "relevance_score": article.relevance_score,
        "keywords": article.keywords or [],
    }
