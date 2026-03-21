from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.user_feature_access import UserFeatureAccess

FEATURE_CATALOG = [
    {
        "feature_key": "dashboard",
        "label": "Dashboard",
        "description": "Main intelligence overview and daily command surface.",
        "category": "core",
        "public_access": False,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "news",
        "label": "News Feed",
        "description": "Curated Dubai and UAE news intelligence feed.",
        "category": "core",
        "public_access": True,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "market",
        "label": "Market",
        "description": "Market overview, predictions, and property valuation workflows.",
        "category": "intelligence",
        "public_access": True,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "analytics",
        "label": "Analytics",
        "description": "Market analytics, insight maps, and opportunity surfaces.",
        "category": "intelligence",
        "public_access": False,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "alerts",
        "label": "Alerts",
        "description": "Alert rules, signal watching, and action prompts.",
        "category": "operations",
        "public_access": False,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "settings",
        "label": "Settings",
        "description": "Workspace configuration, API keys, and white-label controls.",
        "category": "operations",
        "public_access": False,
        "default_authenticated": True,
        "grantable": False,
    },
    {
        "feature_key": "portfolios",
        "label": "Investor Suite",
        "description": "Portfolio management, watchlists, and scoring workflows.",
        "category": "intelligence",
        "public_access": False,
        "default_authenticated": False,
        "grantable": True,
    },
    {
        "feature_key": "competitors",
        "label": "Competitors",
        "description": "Competitive intelligence, tracking, and threat analysis.",
        "category": "intelligence",
        "public_access": False,
        "default_authenticated": False,
        "grantable": True,
    },
    {
        "feature_key": "executive",
        "label": "Executive",
        "description": "Executive dashboards, priorities, and strategy views.",
        "category": "leadership",
        "public_access": False,
        "default_authenticated": False,
        "grantable": True,
    },
    {
        "feature_key": "teams",
        "label": "Teams",
        "description": "Collaboration spaces, shared items, and activity streams.",
        "category": "collaboration",
        "public_access": False,
        "default_authenticated": False,
        "grantable": True,
    },
    {
        "feature_key": "admin_providers",
        "label": "Provider Admin",
        "description": "Operational control center for providers and source health.",
        "category": "admin",
        "public_access": False,
        "default_authenticated": False,
        "grantable": False,
        "admin_only": True,
    },
]


class FeatureAccessService:
    def catalog(self) -> list[dict]:
        return FEATURE_CATALOG

    def _granted_feature_keys(self, grants: Sequence[UserFeatureAccess]) -> set[str]:
        return {grant.feature_key for grant in grants if grant.is_enabled}

    def resolve_access_map(
        self,
        *,
        user: User | None,
        grants: Sequence[UserFeatureAccess] = (),
    ) -> dict[str, bool]:
        if user and user.role == UserRole.ADMIN:
            return {item["feature_key"]: True for item in FEATURE_CATALOG}

        granted_keys = self._granted_feature_keys(grants)
        access_map: dict[str, bool] = {}

        for item in FEATURE_CATALOG:
            feature_key = item["feature_key"]
            if item.get("admin_only"):
                access_map[feature_key] = False
                continue

            if user is None:
                access_map[feature_key] = bool(item["public_access"])
                continue

            access_map[feature_key] = bool(item["default_authenticated"] or feature_key in granted_keys)

        return access_map

    async def get_user_feature_access(self, db: AsyncSession, *, user: User | None) -> list[dict]:
        grants: list[UserFeatureAccess] = []
        if user is not None and user.role != UserRole.ADMIN:
            result = await db.execute(
                select(UserFeatureAccess)
                .where(UserFeatureAccess.user_id == user.id)
                .order_by(UserFeatureAccess.feature_key.asc())
            )
            grants = list(result.scalars().all())

        access_map = self.resolve_access_map(user=user, grants=grants)
        granted_keys = self._granted_feature_keys(grants)

        payload: list[dict] = []
        for item in FEATURE_CATALOG:
            payload.append(
                {
                    **item,
                    "has_access": access_map[item["feature_key"]],
                    "granted_by_admin": item["feature_key"] in granted_keys,
                }
            )
        return payload

    async def list_users(self, db: AsyncSession) -> list[User]:
        result = await db.execute(
            select(User)
            .where(
                User.is_active.is_(True),
                User.role != UserRole.ADMIN,
            )
            .order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def set_user_feature_access(
        self,
        db: AsyncSession,
        *,
        target_user_id: int,
        feature_key: str,
        enabled: bool,
        admin_user_id: int,
    ) -> UserFeatureAccess | None:
        feature = next((item for item in FEATURE_CATALOG if item["feature_key"] == feature_key), None)
        if feature is None:
            raise ValueError("Feature not found")
        if not feature.get("grantable"):
            raise ValueError("This feature is not managed through admin grants")

        result = await db.execute(
            select(UserFeatureAccess).where(
                UserFeatureAccess.user_id == target_user_id,
                UserFeatureAccess.feature_key == feature_key,
            )
        )
        row = result.scalar_one_or_none()

        if enabled:
            if row is None:
                row = UserFeatureAccess(
                    user_id=target_user_id,
                    feature_key=feature_key,
                    is_enabled=True,
                    granted_by_user_id=admin_user_id,
                )
                db.add(row)
            else:
                row.is_enabled = True
                row.granted_by_user_id = admin_user_id
        elif row is not None:
            await db.delete(row)
            row = None

        await db.commit()
        if row is not None:
            await db.refresh(row)
        return row


feature_access_service = FeatureAccessService()
