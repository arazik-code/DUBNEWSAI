from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.mobile import MobileBootstrapResponse, MobileWorkspaceSummary
from app.services.mobile_service import mobile_app_service

router = APIRouter(prefix="/mobile", tags=["mobile"])


@router.get("/bootstrap", response_model=MobileBootstrapResponse)
async def get_mobile_bootstrap(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> MobileBootstrapResponse:
    return await mobile_app_service.build_bootstrap(db, user=current_user)


@router.get("/workspace", response_model=MobileWorkspaceSummary)
async def get_mobile_workspace(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> MobileWorkspaceSummary:
    return await mobile_app_service.build_workspace_summary(db, user=current_user)
