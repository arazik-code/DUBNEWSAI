from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit_breaker import provider_health
from app.database import get_db
from app.dependencies import get_current_admin
from app.models.sources import DataProvider, ProviderFetchLog
from app.models.user import User
from app.services.provider_observability_service import ProviderObservabilityService

router = APIRouter(prefix="/providers", tags=["admin"])


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict[str, object]:
    await ProviderObservabilityService.sync_registry_to_db(db)
    await db.commit()

    result = await db.execute(select(DataProvider).order_by(DataProvider.priority, DataProvider.name))
    providers = result.scalars().all()

    by_type: dict[str, dict[str, int]] = {}
    healthy_count = 0
    unhealthy_count = 0
    for provider in providers:
        stats = by_type.setdefault(provider.type, {"total": 0, "enabled": 0, "healthy": 0})
        stats["total"] += 1
        if provider.is_enabled:
            stats["enabled"] += 1
        if provider.is_healthy:
            stats["healthy"] += 1
            healthy_count += 1
        else:
            unhealthy_count += 1

    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = await db.scalar(
        select(func.count(ProviderFetchLog.id)).where(ProviderFetchLog.created_at >= start_of_day)
    )

    return {
        "total_providers": len(providers),
        "healthy": healthy_count,
        "unhealthy": unhealthy_count,
        "by_type": by_type,
        "total_calls_today": calls_today or 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/")
async def get_all_providers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[dict[str, object]]:
    await ProviderObservabilityService.sync_registry_to_db(db)
    await db.commit()

    result = await db.execute(select(DataProvider).order_by(DataProvider.priority, DataProvider.name))
    providers = result.scalars().all()
    health_report = provider_health.get_health_report()

    items: list[dict[str, object]] = []
    for provider in providers:
        live_state = health_report.get(provider.name, {})
        total_calls = provider.total_calls or 0
        success_rate = round(((provider.successful_calls or 0) / total_calls) * 100, 2) if total_calls else 0.0
        items.append(
            {
                "id": provider.id,
                "name": provider.name,
                "type": provider.type,
                "priority": provider.priority,
                "is_enabled": provider.is_enabled,
                "is_healthy": provider.is_healthy,
                "reliability_score": provider.reliability_score,
                "total_calls": total_calls,
                "successful_calls": provider.successful_calls or 0,
                "failed_calls": provider.failed_calls or 0,
                "success_rate": success_rate,
                "last_success_at": provider.last_success_at,
                "last_failure_at": provider.last_failure_at,
                "circuit_state": provider.circuit_state,
                "rate_limit_per_day": provider.rate_limit_per_day,
                "cost_per_call": provider.cost_per_call,
                "base_url": provider.base_url,
                "live_health_score": live_state.get("health_score", provider.reliability_score),
                "live_circuit_state": live_state.get("circuit_state", provider.circuit_state),
            }
        )
    return items


@router.get("/{provider_id}/logs")
async def get_provider_logs(
    provider_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[dict[str, object]]:
    result = await db.execute(
        select(ProviderFetchLog)
        .where(ProviderFetchLog.provider_id == provider_id)
        .order_by(ProviderFetchLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "status": log.status,
            "items_fetched": log.items_fetched,
            "response_time_ms": log.response_time_ms,
            "error_message": log.error_message,
            "error_type": log.error_type,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/{provider_id}/stats")
async def get_provider_stats(
    provider_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict[str, object]:
    provider = await db.scalar(select(DataProvider).where(DataProvider.id == provider_id))
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(ProviderFetchLog).where(
            and_(
                ProviderFetchLog.provider_id == provider_id,
                ProviderFetchLog.created_at >= since,
            )
        )
    )
    logs = result.scalars().all()

    total_fetches = len(logs)
    successful = len([log for log in logs if log.status == "success"])
    failed = len([log for log in logs if log.status != "success"])
    avg_response_time = (
        round(sum(log.response_time_ms for log in logs if log.response_time_ms) / total_fetches, 2)
        if total_fetches
        else 0.0
    )
    total_items = sum(log.items_fetched for log in logs)

    daily_breakdown: dict[str, dict[str, int]] = {}
    for log in logs:
        key = log.created_at.date().isoformat()
        bucket = daily_breakdown.setdefault(key, {"success": 0, "failure": 0, "items": 0})
        if log.status == "success":
            bucket["success"] += 1
            bucket["items"] += log.items_fetched
        else:
            bucket["failure"] += 1

    return {
        "provider": {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
        },
        "period_days": days,
        "totals": {
            "total_fetches": total_fetches,
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / total_fetches) * 100, 2) if total_fetches else 0.0,
            "total_items_fetched": total_items,
            "avg_response_time_ms": avg_response_time,
        },
        "daily_breakdown": [
            {
                "date": date_key,
                **values,
            }
            for date_key, values in sorted(daily_breakdown.items())
        ],
    }


@router.patch("/{provider_id}/toggle")
async def toggle_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict[str, object]:
    provider = await db.scalar(select(DataProvider).where(DataProvider.id == provider_id))
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.is_enabled = not provider.is_enabled
    await db.commit()
    return {"id": provider.id, "name": provider.name, "is_enabled": provider.is_enabled}


@router.post("/{provider_id}/reset-circuit")
async def reset_circuit_breaker(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict[str, str]:
    provider = await db.scalar(select(DataProvider).where(DataProvider.id == provider_id))
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_health.reset(provider.name)
    provider.circuit_state = "closed"
    provider.circuit_opened_at = None
    provider.failure_count = 0
    provider.is_healthy = True
    provider.last_failure_at = None
    await db.commit()
    return {"message": f"Circuit breaker reset for {provider.name}"}
