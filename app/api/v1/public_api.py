from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache
from app.database import get_db
from app.models.api_access import APIKey, Webhook
from app.models.news import NewsArticle
from app.schemas.enterprise import WebhookRegisterRequest
from app.services.ai_service import AIService
from app.services.market_service import MarketService
from app.services.predictive import forecast_service

settings = get_settings()
router = APIRouter(prefix="/public/v1", tags=["Public API"])


async def api_key_auth(
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    if not settings.PUBLIC_API_ENABLED:
        raise HTTPException(status_code=404, detail="Public API is disabled")

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == hashlib.sha256(x_api_key.encode()).hexdigest(),
            APIKey.is_active.is_(True),
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    rate_key = f"public-api:{api_key.id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
    current = await cache.increment(rate_key)
    if current == 1:
        await cache.expire(rate_key, 3600)
    if current > api_key.rate_limit_per_hour:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    api_key.total_requests += 1
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return api_key


@router.get("/market/overview")
async def get_market_overview(
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth),
) -> dict:
    del api_key
    stocks = await MarketService.get_latest_market_data(db, limit=12)
    gainers = sorted(stocks, key=lambda item: item.change_percent or 0, reverse=True)[:3]
    losers = sorted(stocks, key=lambda item: item.change_percent or 0)[:3]
    return {
        "region": "UAE",
        "market_status": "live",
        "indices": [{"symbol": item.symbol, "name": item.name, "price": item.price, "change_percent": item.change_percent} for item in stocks[:5]],
        "top_movers": {
            "gainers": [{"symbol": item.symbol, "price": item.price, "change_percent": item.change_percent} for item in gainers],
            "losers": [{"symbol": item.symbol, "price": item.price, "change_percent": item.change_percent} for item in losers],
        },
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/news/latest")
async def get_latest_news(
    limit: int = 10,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth),
) -> dict:
    del api_key
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.is_published.is_(True)).order_by(NewsArticle.published_at.desc()).limit(limit * 3)
    )
    articles = list(result.scalars().all())
    if category:
        articles = [item for item in articles if item.category.value == category]
    articles = articles[:limit]
    return {
        "articles": [
            {
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "source": item.source_name or item.source.value,
                "published_at": item.published_at,
                "category": item.category.value,
                "sentiment": item.sentiment.value if item.sentiment else None,
            }
            for item in articles
        ],
        "total": len(articles),
    }


@router.get("/analytics/sentiment")
async def get_sentiment_analysis(
    symbol: str | None = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth),
) -> dict:
    del api_key
    if symbol:
        return await AIService.get_symbol_sentiment(db, symbol=symbol, days=days)
    return await AIService.get_overall_sentiment(db, days=days)


@router.get("/predictions/price")
async def get_price_prediction(
    symbol: str,
    days_ahead: int = 30,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth),
) -> dict:
    del api_key
    return await forecast_service.predict_price_movement(db, symbol.upper(), days_ahead=days_ahead)


@router.post("/webhooks/register")
async def register_webhook(
    payload: WebhookRegisterRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth),
) -> dict:
    webhook = Webhook(api_key_id=api_key.id, url=payload.webhook_url, events=payload.events, is_active=True)
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return {"webhook_id": webhook.id, "status": "active"}
