from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin.providers import router as providers_router
from app.database import get_db
from app.dependencies import get_current_admin
from app.models.news import NewsArticle
from app.models.user import User
from app.tasks.news_tasks import fetch_newsapi_articles, fetch_rss_feeds

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(providers_router)


@router.get("/stats")
async def get_admin_stats(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_news = await db.scalar(select(func.count()).select_from(NewsArticle))
    return {
        "users": total_users or 0,
        "news_articles": total_news or 0,
    }


@router.post("/trigger-news-fetch", status_code=status.HTTP_202_ACCEPTED)
async def trigger_news_fetch(_: User = Depends(get_current_admin)) -> dict[str, str]:
    newsapi_task = fetch_newsapi_articles.delay()
    rss_task = fetch_rss_feeds.delay()
    return {
        "status": "queued",
        "newsapi_task_id": newsapi_task.id,
        "rss_task_id": rss_task.id,
    }
