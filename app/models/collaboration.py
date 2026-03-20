from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Team(BaseModel):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    shared_portfolios: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    shared_watchlists: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    shared_insights: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    shared_items: Mapped[list["SharedItem"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    team_activity: Mapped[list["TeamActivity"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class TeamMember(BaseModel):
    __tablename__ = "team_members"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    team: Mapped["Team"] = relationship(back_populates="members")
    user = relationship("User")

    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_user"),)


class SharedItem(BaseModel):
    __tablename__ = "shared_items"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_comment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="shared_items")
    shared_by = relationship("User")
    comments: Mapped[list["ItemComment"]] = relationship(back_populates="shared_item", cascade="all, delete-orphan")


class ItemComment(BaseModel):
    __tablename__ = "item_comments"

    shared_item_id: Mapped[int] = mapped_column(ForeignKey("shared_items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    parent_comment_id: Mapped[int | None] = mapped_column(ForeignKey("item_comments.id", ondelete="CASCADE"), nullable=True)

    shared_item: Mapped["SharedItem"] = relationship(back_populates="comments")
    user = relationship("User")
    replies: Mapped[list["ItemComment"]] = relationship(back_populates="parent")
    parent: Mapped["ItemComment | None"] = relationship(remote_side="ItemComment.id", back_populates="replies")


class TeamActivity(BaseModel):
    __tablename__ = "team_activity"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activity_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="team_activity")
    user = relationship("User")
