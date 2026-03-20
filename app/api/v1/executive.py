from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import require_premium
from app.models.user import User
from app.services.executive import executive_dashboard

settings = get_settings()
router = APIRouter(prefix="/executive", tags=["executive"])


def _ensure_enabled() -> None:
    if not settings.EXECUTIVE_FEATURES:
        raise HTTPException(status_code=404, detail="Executive features are disabled")


@router.get("/dashboard")
async def get_executive_dashboard(
    time_period: str = Query(default="30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    return await executive_dashboard.generate_executive_summary(db, time_period=time_period)


@router.get("/summary")
async def get_executive_summary(
    time_period: str = Query(default="30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    _ensure_enabled()
    payload = await executive_dashboard.generate_executive_summary(db, time_period=time_period)
    return payload["summary"]


@router.get("/priorities")
async def get_executive_priorities(
    time_period: str = Query(default="30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[dict]:
    del current_user
    _ensure_enabled()
    payload = await executive_dashboard.generate_executive_summary(db, time_period=time_period)
    return payload["strategic_priorities"]
