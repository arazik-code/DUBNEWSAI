from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WhiteLabelConfig(BaseModel):
    __tablename__ = "white_label_configs"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(200), nullable=True, unique=True)
    subdomain: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    enabled_features: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    api_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    api_rate_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
