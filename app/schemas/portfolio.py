from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.portfolio import PortfolioType, TransactionType


class PortfolioCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    portfolio_type: PortfolioType = PortfolioType.MIXED
    base_currency: str = Field(default="AED", min_length=3, max_length=3)


class PortfolioTransactionCreateRequest(BaseModel):
    transaction_type: TransactionType
    symbol: str = Field(min_length=1, max_length=50)
    quantity: float
    price: float
    transaction_date: datetime
    fees: float = 0.0
    notes: str | None = Field(default=None, max_length=500)


class WatchlistCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    alert_on_change: bool = False
    change_threshold_percent: float = 5.0


class WatchlistItemCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=50)
    asset_type: str | None = Field(default=None, max_length=50)
    asset_name: str | None = Field(default=None, max_length=200)
    target_buy_price: float | None = None
    target_sell_price: float | None = None
    notes: str | None = Field(default=None, max_length=1000)
    tags: list[str] = []


class InvestmentScoreRequest(BaseModel):
    risk_profile: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")


class PortfolioHoldingResponse(BaseModel):
    id: int
    symbol: str
    asset_type: str | None = None
    asset_name: str | None = None
    quantity: float
    average_cost: float
    current_price: float | None = None
    current_value: float | None = None
    unrealized_gain_loss: float | None = None
    unrealized_gain_loss_percent: float | None = None
    realized_gain_loss: float | None = None
    total_dividends: float
    purchase_date: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PortfolioTransactionResponse(BaseModel):
    id: int
    transaction_type: TransactionType
    symbol: str
    quantity: float
    price: float
    total_amount: float
    fees: float
    tax: float
    transaction_date: datetime
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    portfolio_type: PortfolioType
    base_currency: str
    is_public: bool
    auto_update: bool
    total_value_aed: float
    total_cost_aed: float
    total_return_aed: float
    total_return_percent: float
    last_updated: datetime | None = None
    holdings: list[PortfolioHoldingResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    asset_type: str | None = None
    asset_name: str | None = None
    target_buy_price: float | None = None
    target_sell_price: float | None = None
    notes: str | None = None
    tags: list[str] | None = None
    added_price: float | None = None
    current_price: float | None = None
    price_change_percent: float | None = None

    model_config = ConfigDict(from_attributes=True)


class WatchlistResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    alert_on_change: bool
    change_threshold_percent: float
    items: list[WatchlistItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PortfolioAnalyticsResponse(BaseModel):
    overview: dict
    allocation: dict
    performance: dict
    risk_metrics: dict
    top_performers: list[dict]
    bottom_performers: list[dict]
    dividend_income: dict


class InvestmentScoreResponse(BaseModel):
    symbol: str
    overall_score: float
    component_scores: dict[str, float]
    recommendation: str
    confidence: str
    rationale: str
    key_factors: list[str]
    risks: list[str]
    target_price: float
    stop_loss: float
    time_horizon: str
    generated_at: datetime
