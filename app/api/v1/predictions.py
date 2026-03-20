from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.user import User
from app.services.predictive import forecast_service

settings = get_settings()
router = APIRouter(prefix="/predictions", tags=["predictions"])


def _ensure_enabled() -> None:
    if not settings.ENABLE_PREDICTIONS:
        raise HTTPException(status_code=404, detail="Predictions are disabled")


@router.get("/price/{symbol}")
async def get_price_prediction(
    symbol: str,
    days_ahead: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    payload = await forecast_service.predict_price_movement(db, symbol.upper(), days_ahead=days_ahead)
    if "error" in payload:
        raise HTTPException(status_code=422, detail=payload["error"])
    return payload


@router.get("/options")
async def get_prediction_options(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    return await forecast_service.get_prediction_universe(db)


@router.get("/market-trend")
async def get_market_trend_prediction(
    region: str = Query(default="UAE"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    return await forecast_service.predict_market_trend(db, region=region)


@router.get("/property-trend")
async def get_property_trend_prediction(
    location: str = Query(..., min_length=2),
    property_type: str = Query(default="apartment"),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    payload = await forecast_service.predict_property_value_trend(location=location, property_type=property_type)
    if "error" in payload:
        raise HTTPException(status_code=422, detail=payload["error"])
    return payload
