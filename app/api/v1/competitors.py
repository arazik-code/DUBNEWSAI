from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional, require_premium
from app.models.user import User
from app.schemas.enterprise import CompetitorCreateRequest, CompetitorResponse
from app.services.competitive_intelligence import competitor_service

router = APIRouter(prefix="/competitors", tags=["competitors"])


async def _ensure_seeded(db: AsyncSession) -> None:
    existing = await competitor_service.list_competitors(db)
    if existing:
        return
    defaults = [
        {"name": "Emaar Properties", "industry": "Real Estate", "sector": "Real Estate", "ticker_symbol": "EMAAR.DU", "market_share_percent": 18.0, "revenue_growth_rate": 13.0, "market_cap": 22_000_000_000, "headquarters": "Dubai", "tags": ["developer", "uae", "residential"]},
        {"name": "Aldar Properties", "industry": "Real Estate", "sector": "Real Estate", "ticker_symbol": "ALDAR.AD", "market_share_percent": 15.0, "revenue_growth_rate": 12.0, "market_cap": 19_000_000_000, "headquarters": "Abu Dhabi", "tags": ["developer", "uae", "masterplan"]},
        {"name": "DAMAC Properties", "industry": "Real Estate", "sector": "Real Estate", "ticker_symbol": "DAMAC.DU", "market_share_percent": 9.0, "revenue_growth_rate": 17.0, "market_cap": 9_000_000_000, "headquarters": "Dubai", "tags": ["luxury", "developer"]},
        {"name": "DFM", "industry": "Capital Markets", "sector": "Financial Services", "ticker_symbol": "DFM.DU", "market_share_percent": 27.0, "revenue_growth_rate": 8.0, "market_cap": 6_000_000_000, "headquarters": "Dubai", "tags": ["exchange", "market-infrastructure"]},
    ]
    for payload in defaults:
        await competitor_service.create_competitor(db, **payload)


@router.get("/", response_model=list[CompetitorResponse])
async def list_competitors(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[CompetitorResponse]:
    del current_user
    await _ensure_seeded(db)
    competitors = await competitor_service.list_competitors(db)
    return [CompetitorResponse.model_validate(item) for item in competitors]


@router.post("/", response_model=CompetitorResponse)
async def create_competitor(
    payload: CompetitorCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> CompetitorResponse:
    del current_user
    competitor = await competitor_service.create_competitor(db, **payload.model_dump())
    return CompetitorResponse.model_validate(competitor)


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> CompetitorResponse:
    del current_user
    competitor = await competitor_service.get_competitor(db, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return CompetitorResponse.model_validate(competitor)


@router.get("/{competitor_id}/analysis")
async def get_competitor_analysis(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    try:
        return await competitor_service.analyze_competitor(db, competitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{competitor_id}/swot")
async def get_competitor_swot(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    try:
        return await competitor_service.get_swot(db, competitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{competitor_id}/news")
async def get_competitor_news(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    try:
        return await competitor_service.get_news(db, competitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
