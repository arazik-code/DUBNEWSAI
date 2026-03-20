from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collaboration import SharedItem, Team, TeamActivity, TeamMember


class TeamService:
    async def list_teams_for_user(self, db: AsyncSession, *, user_id: int) -> list[Team]:
        result = await db.execute(
            select(Team)
            .options(
                selectinload(Team.members),
                selectinload(Team.shared_items),
                selectinload(Team.team_activity),
            )
            .join(TeamMember, TeamMember.team_id == Team.id, isouter=True)
            .where(or_(Team.owner_id == user_id, TeamMember.user_id == user_id))
            .order_by(Team.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def create_team(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        name: str,
        description: str | None = None,
        max_members: int = 10,
        shared_portfolios: bool = True,
        shared_watchlists: bool = True,
        shared_insights: bool = True,
    ) -> Team:
        team = Team(
            owner_id=owner_id,
            name=name,
            description=description,
            max_members=max_members,
            shared_portfolios=shared_portfolios,
            shared_watchlists=shared_watchlists,
            shared_insights=shared_insights,
        )
        db.add(team)
        await db.flush()
        db.add(
            TeamMember(
                team_id=team.id,
                user_id=owner_id,
                role="owner",
                can_edit=True,
                can_share=True,
                can_delete=True,
            )
        )
        db.add(
            TeamActivity(
                team_id=team.id,
                user_id=owner_id,
                activity_type="team_created",
                description=f"Created team {name}",
                activity_metadata={"name": name},
            )
        )
        await db.commit()
        await db.refresh(team)
        return team

    async def add_member(
        self,
        db: AsyncSession,
        *,
        team_id: int,
        actor_id: int,
        user_id: int,
        role: str = "member",
        can_edit: bool = False,
        can_share: bool = False,
        can_delete: bool = False,
    ) -> TeamMember:
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            can_edit=can_edit,
            can_share=can_share,
            can_delete=can_delete,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(member)
        db.add(
            TeamActivity(
                team_id=team_id,
                user_id=actor_id,
                activity_type="member_added",
                description=f"Added member {user_id} as {role}",
                activity_metadata={"member_user_id": user_id, "role": role},
            )
        )
        await db.commit()
        await db.refresh(member)
        return member

    async def share_item(
        self,
        db: AsyncSession,
        *,
        team_id: int,
        shared_by_user_id: int,
        item_type: str,
        item_id: int,
        item_name: str | None = None,
        can_edit: bool = False,
        can_comment: bool = True,
        description: str | None = None,
    ) -> SharedItem:
        shared_item = SharedItem(
            team_id=team_id,
            shared_by_user_id=shared_by_user_id,
            item_type=item_type,
            item_id=item_id,
            item_name=item_name,
            can_edit=can_edit,
            can_comment=can_comment,
            description=description,
            shared_at=datetime.now(timezone.utc),
        )
        db.add(shared_item)
        db.add(
            TeamActivity(
                team_id=team_id,
                user_id=shared_by_user_id,
                activity_type="shared",
                description=f"Shared {item_type} {item_name or item_id}",
                activity_metadata={"item_type": item_type, "item_id": item_id, "item_name": item_name},
            )
        )
        await db.commit()
        await db.refresh(shared_item)
        return shared_item

    async def get_team_activity(self, db: AsyncSession, *, team_id: int) -> list[dict[str, Any]]:
        result = await db.execute(
            select(TeamActivity)
            .options(selectinload(TeamActivity.user))
            .where(TeamActivity.team_id == team_id)
            .order_by(TeamActivity.created_at.desc())
            .limit(100)
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": row.id,
                "activity_type": row.activity_type,
                "description": row.description,
                "metadata": row.activity_metadata or {},
                "created_at": row.created_at,
                "user": {
                    "id": row.user.id,
                    "full_name": row.user.full_name,
                    "email": row.user.email,
                }
                if row.user is not None
                else None,
            }
            for row in rows
        ]

    async def ensure_team_access(self, db: AsyncSession, *, team_id: int, user_id: int) -> Team | None:
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.members), selectinload(Team.shared_items))
            .where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        if team is None:
            return None
        if team.owner_id == user_id:
            return team
        if any(member.user_id == user_id and member.is_active for member in team.members):
            return team
        return None


team_service = TeamService()
