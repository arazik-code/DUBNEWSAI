from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.market_data import WeatherSnapshotResponse
from app.schemas.user import UserResponse


class MobileArticleCard(BaseModel):
    id: int
    title: str
    description: str | None = None
    source_name: str | None = None
    category: str
    sentiment: str
    published_at: datetime
    image_url: str | None = None
    relevance_score: int = 0


class MobileMarketCard(BaseModel):
    symbol: str
    name: str
    price: float
    change_percent: float
    currency: str = "AED"
    exchange: str | None = None
    market_type: str | None = None


class MobileFeatureAccessCard(BaseModel):
    feature_key: str
    label: str
    description: str | None = None
    category: str
    has_access: bool
    public_access: bool
    grantable: bool


class MobileMarketPulse(BaseModel):
    market_status: dict[str, str] | None = None
    movers: list[MobileMarketCard]
    real_estate_leaders: list[MobileMarketCard]
    weather: WeatherSnapshotResponse | None = None
    trend_prediction: dict[str, Any] | None = None


class MobilePortfolioHoldingCard(BaseModel):
    symbol: str
    asset_name: str | None = None
    current_value: float = 0.0
    return_percent: float = 0.0


class MobilePortfolioSnapshot(BaseModel):
    portfolio_count: int
    watchlist_count: int
    total_value_aed: float
    total_return_percent: float
    watch_items: int
    top_holdings: list[MobilePortfolioHoldingCard]


class MobileNotificationCard(BaseModel):
    id: int
    title: str
    message: str
    priority: str
    created_at: datetime
    is_read: bool


class MobileNotificationsSnapshot(BaseModel):
    unread_count: int
    latest: list[MobileNotificationCard]


class MobileAlertsSnapshot(BaseModel):
    summary: dict[str, Any]
    recent_triggers: list[dict[str, Any]]
    templates: list[dict[str, Any]]


class MobileCompetitorSpotlight(BaseModel):
    id: int
    name: str
    ticker_symbol: str | None = None
    market_share_percent: float | None = None
    threat_level: str | None = None
    strategic_note: str | None = None


class MobileWorkspaceSummary(BaseModel):
    user: UserResponse
    enabled_features: list[str]
    portfolios: MobilePortfolioSnapshot | None = None
    alerts: MobileAlertsSnapshot | None = None
    notifications: MobileNotificationsSnapshot
    teams_count: int = 0
    competitor_spotlight: MobileCompetitorSpotlight | None = None


class MobileBootstrapResponse(BaseModel):
    app_name: str
    app_version: str
    feature_access: list[MobileFeatureAccessCard]
    hero_article: MobileArticleCard | None = None
    featured_articles: list[MobileArticleCard]
    trending_articles: list[MobileArticleCard]
    market_pulse: MobileMarketPulse
    prediction_universe: dict[str, Any]
    property_options: dict[str, Any]
    workspace_summary: MobileWorkspaceSummary | None = None
