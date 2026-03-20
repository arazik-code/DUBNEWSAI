from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_kwargs

if TYPE_CHECKING:
    from app.models.alert import Alert, Automation
    from app.models.api_access import APIKey
    from app.models.collaboration import Team, TeamMember
    from app.models.notification import Notification
    from app.models.portfolio import InvestmentRecommendation, Portfolio, Watchlist
    from app.models.subscription import Subscription
    from app.models.user_preference import UserPreference
    from app.models.white_label import WhiteLabelConfig


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role", **enum_kwargs(UserRole)),
        default=UserRole.USER,
        nullable=False,
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    automations: Mapped[list["Automation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    investment_recommendations: Mapped[list["InvestmentRecommendation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(cascade="all, delete-orphan")
    owned_teams: Mapped[list["Team"]] = relationship(foreign_keys="Team.owner_id")
    team_memberships: Mapped[list["TeamMember"]] = relationship(cascade="all, delete-orphan")
    white_label_configs: Mapped[list["WhiteLabelConfig"]] = relationship(cascade="all, delete-orphan")
