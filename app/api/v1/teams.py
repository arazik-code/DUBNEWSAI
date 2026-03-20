from __future__ import annotations

from sqlalchemy import or_, select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.enterprise import SharedItemCreateRequest, TeamCreateRequest, TeamMemberCreateRequest, TeamResponse
from app.services.collaboration import team_service

settings = get_settings()
router = APIRouter(prefix="/teams", tags=["teams"])


def _ensure_enabled() -> None:
    if not settings.ENABLE_TEAM_FEATURES:
        raise HTTPException(status_code=404, detail="Team features are disabled")


@router.get("/", response_model=list[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[TeamResponse]:
    _ensure_enabled()
    teams = await team_service.list_teams_for_user(db, user_id=current_user.id)
    return [TeamResponse.model_validate(item) for item in teams]


@router.get("/directory")
async def get_team_directory(
    query: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[dict]:
    _ensure_enabled()
    statement = select(User).where(User.id != current_user.id, User.is_active.is_(True)).order_by(User.full_name.asc().nullslast(), User.email.asc()).limit(20)
    if query.strip():
        like_query = f"%{query.strip()}%"
        statement = statement.where(or_(User.email.ilike(like_query), User.full_name.ilike(like_query)))
    result = await db.execute(statement)
    users = result.scalars().all()
    return [{"id": item.id, "full_name": item.full_name, "email": item.email, "role": item.role.value} for item in users]


@router.post("/", response_model=TeamResponse)
async def create_team(
    payload: TeamCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> TeamResponse:
    _ensure_enabled()
    team = await team_service.create_team(db, owner_id=current_user.id, **payload.model_dump())
    return TeamResponse.model_validate(team)


@router.post("/{team_id}/members")
async def add_team_member(
    team_id: int,
    payload: TeamMemberCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    _ensure_enabled()
    team = await team_service.ensure_team_access(db, team_id=team_id, user_id=current_user.id)
    if team is None or team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team owners can add members")
    if len(team.members) >= team.max_members:
        raise HTTPException(status_code=400, detail="Team member limit reached")
    member = await team_service.add_member(db, team_id=team_id, actor_id=current_user.id, **payload.model_dump())
    return {"id": member.id, "team_id": member.team_id, "user_id": member.user_id, "role": member.role}


@router.post("/{team_id}/share")
async def share_team_item(
    team_id: int,
    payload: SharedItemCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    _ensure_enabled()
    team = await team_service.ensure_team_access(db, team_id=team_id, user_id=current_user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    shared_item = await team_service.share_item(db, team_id=team_id, shared_by_user_id=current_user.id, **payload.model_dump())
    return {
        "id": shared_item.id,
        "team_id": shared_item.team_id,
        "item_type": shared_item.item_type,
        "item_id": shared_item.item_id,
        "item_name": shared_item.item_name,
    }


@router.get("/{team_id}/activity")
async def get_team_activity(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[dict]:
    _ensure_enabled()
    team = await team_service.ensure_team_access(db, team_id=team_id, user_id=current_user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return await team_service.get_team_activity(db, team_id=team_id)
