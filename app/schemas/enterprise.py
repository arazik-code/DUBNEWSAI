from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompetitorCreateRequest(BaseModel):
    name: str
    official_name: str | None = None
    industry: str | None = None
    sector: str | None = None
    headquarters: str | None = None
    ticker_symbol: str | None = None
    website: str | None = None
    description: str | None = None
    founded_year: int | None = None
    employee_count: int | None = None
    market_cap: float | None = None
    revenue_annual: float | None = None
    revenue_growth_rate: float | None = None
    profit_margin: float | None = None
    market_share_percent: float | None = None
    competitive_strength_score: float | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class CompetitorResponse(BaseModel):
    id: int
    name: str
    official_name: str | None = None
    industry: str | None = None
    sector: str | None = None
    headquarters: str | None = None
    ticker_symbol: str | None = None
    website: str | None = None
    description: str | None = None
    founded_year: int | None = None
    employee_count: int | None = None
    market_cap: float | None = None
    revenue_annual: float | None = None
    revenue_growth_rate: float | None = None
    profit_margin: float | None = None
    market_share_percent: float | None = None
    competitive_strength_score: float | None = None
    is_active: bool
    last_analyzed: datetime | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamCreateRequest(BaseModel):
    name: str
    description: str | None = None
    max_members: int = Field(default=10, ge=2, le=100)
    shared_portfolios: bool = True
    shared_watchlists: bool = True
    shared_insights: bool = True


class TeamMemberCreateRequest(BaseModel):
    user_id: int
    role: str = "member"
    can_edit: bool = False
    can_share: bool = False
    can_delete: bool = False


class SharedItemCreateRequest(BaseModel):
    item_type: str
    item_id: int
    item_name: str | None = None
    can_edit: bool = False
    can_comment: bool = True
    description: str | None = None


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int
    is_active: bool
    max_members: int
    shared_portfolios: bool
    shared_watchlists: bool
    shared_insights: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WhiteLabelConfigRequest(BaseModel):
    company_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    custom_domain: str | None = None
    subdomain: str | None = None
    enabled_features: list[str] = Field(default_factory=list)
    api_enabled: bool = False
    api_rate_limit: int = Field(default=100, ge=10, le=100000)
    is_active: bool = True


class WhiteLabelConfigResponse(BaseModel):
    id: int
    company_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    custom_domain: str | None = None
    subdomain: str | None = None
    enabled_features: list[str] | None = None
    api_enabled: bool
    api_rate_limit: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreateRequest(BaseModel):
    name: str
    rate_limit_per_hour: int = Field(default=100, ge=10, le=100000)
    scopes: list[str] = Field(default_factory=lambda: ["market.read", "news.read", "analytics.read"])


class APIKeyResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    rate_limit_per_hour: int
    total_requests: int
    last_used_at: datetime | None = None
    scopes: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    plaintext_key: str


class WebhookRegisterRequest(BaseModel):
    webhook_url: str
    events: list[str]
