from __future__ import annotations

import hashlib
import secrets

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import require_premium
from app.models.api_access import APIKey
from app.models.user import User
from app.models.white_label import WhiteLabelConfig
from app.schemas.enterprise import (
    APIKeyCreateRequest,
    APIKeyCreatedResponse,
    APIKeyResponse,
    WhiteLabelConfigRequest,
    WhiteLabelConfigResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[APIKeyResponse]:
    result = await db.execute(select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc()))
    return [APIKeyResponse.model_validate(item) for item in result.scalars().all()]


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    payload: APIKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> APIKeyCreatedResponse:
    plaintext = f"dna_{secrets.token_urlsafe(24)}"
    record = APIKey(
        user_id=current_user.id,
        name=payload.name,
        key_hash=hashlib.sha256(plaintext.encode()).hexdigest(),
        rate_limit_per_hour=payload.rate_limit_per_hour,
        scopes=payload.scopes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return APIKeyCreatedResponse.model_validate({**record.__dict__, "plaintext_key": plaintext})


@router.get("/white-label", response_model=WhiteLabelConfigResponse | None)
async def get_white_label_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> WhiteLabelConfigResponse | None:
    result = await db.execute(select(WhiteLabelConfig).where(WhiteLabelConfig.user_id == current_user.id))
    row = result.scalar_one_or_none()
    return WhiteLabelConfigResponse.model_validate(row) if row is not None else None


@router.put("/white-label", response_model=WhiteLabelConfigResponse)
async def upsert_white_label_config(
    payload: WhiteLabelConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_premium),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> WhiteLabelConfigResponse:
    result = await db.execute(select(WhiteLabelConfig).where(WhiteLabelConfig.user_id == current_user.id))
    row = result.scalar_one_or_none()
    if row is None:
        row = WhiteLabelConfig(user_id=current_user.id, **payload.model_dump())
        db.add(row)
    else:
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return WhiteLabelConfigResponse.model_validate(row)
