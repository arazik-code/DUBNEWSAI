from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.enterprise import CompetitorCreateRequest, CompetitorResponse
from app.services.competitive_intelligence import competitor_service

router = APIRouter(prefix="/competitors", tags=["competitors"])

COMPETITOR_CATALOG = [
    {
        "name": "Emaar Properties",
        "industry": "Real Estate",
        "sector": "Real Estate",
        "ticker_symbol": "EMAAR.DU",
        "market_share_percent": 18.0,
        "revenue_growth_rate": 13.0,
        "market_cap": 22_000_000_000,
        "headquarters": "Dubai",
        "tags": ["developer", "uae", "residential"],
        "description": "Dubai market bellwether with broad residential, hospitality, and community exposure.",
    },
    {
        "name": "Aldar Properties",
        "industry": "Real Estate",
        "sector": "Real Estate",
        "ticker_symbol": "ALDAR.AD",
        "market_share_percent": 15.0,
        "revenue_growth_rate": 12.0,
        "market_cap": 19_000_000_000,
        "headquarters": "Abu Dhabi",
        "tags": ["developer", "uae", "masterplan"],
        "description": "Abu Dhabi developer with masterplan communities and institutional-grade delivery profile.",
    },
    {
        "name": "DAMAC Properties",
        "industry": "Real Estate",
        "sector": "Real Estate",
        "ticker_symbol": "DAMAC.DU",
        "market_share_percent": 9.0,
        "revenue_growth_rate": 17.0,
        "market_cap": 9_000_000_000,
        "headquarters": "Dubai",
        "tags": ["luxury", "developer"],
        "description": "Luxury-focused Dubai developer with stronger premium positioning and cyclical sensitivity.",
    },
    {
        "name": "DFM",
        "industry": "Capital Markets",
        "sector": "Financial Services",
        "ticker_symbol": "DFM.DU",
        "market_share_percent": 27.0,
        "revenue_growth_rate": 8.0,
        "market_cap": 6_000_000_000,
        "headquarters": "Dubai",
        "tags": ["exchange", "market-infrastructure"],
        "description": "Dubai market infrastructure player that reflects trading activity and local capital market depth.",
    },
]
@router.get("", response_model=list[CompetitorResponse], include_in_schema=False)
@router.get("/", response_model=list[CompetitorResponse])
async def list_competitors(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[CompetitorResponse]:
    del current_user
    competitors = await competitor_service.list_competitors(db)
    return [CompetitorResponse.model_validate(item) for item in competitors]


@router.get("/catalog")
async def get_competitor_catalog(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[dict]:
    del current_user
    competitors = await competitor_service.list_competitors(db)
    tracked_names = {item.name for item in competitors}
    payload: list[dict] = []
    for item in COMPETITOR_CATALOG:
        payload.append({**item, "tracked": item["name"] in tracked_names})
    return payload


@router.post("", response_model=CompetitorResponse, include_in_schema=False)
@router.post("/", response_model=CompetitorResponse)
async def create_competitor(
    payload: CompetitorCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
