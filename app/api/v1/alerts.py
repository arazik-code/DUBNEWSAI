from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.alert import Alert, AlertFrequency, AlertStatus, AlertType
from app.models.user import User
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    name: str
    alert_type: AlertType
    symbol: str | None = None
    keywords: list[str] | None = None
    threshold_value: float | None = None
    category: str | None = None
    conditions: dict[str, object] | None = None
    frequency: AlertFrequency = AlertFrequency.INSTANT
    email_enabled: bool = False
    notification_enabled: bool = True
    webhook_url: str | None = None


class AlertResponse(BaseModel):
    id: int
    name: str
    alert_type: AlertType
    status: AlertStatus
    symbol: str | None = None
    keywords: list[str] | None = None
    threshold_value: float | None = None
    category: str | None = None
    frequency: AlertFrequency
    trigger_count: int
    last_triggered_at: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    alert = await AlertService.create_alert(db, current_user.id, alert_data.model_dump())
    return AlertResponse.model_validate(alert)


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    alerts = await AlertService.get_user_alerts(db, current_user.id)
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/intelligence")
async def get_alert_intelligence(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AlertService.get_alert_intelligence(db, current_user.id)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await AlertService.delete_alert(db, alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert deleted"}


@router.patch("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_active = not alert.is_active
    alert.status = AlertStatus.ACTIVE if alert.is_active else AlertStatus.PAUSED
    await db.commit()

    return {"message": f"Alert {'activated' if alert.is_active else 'deactivated'}"}
