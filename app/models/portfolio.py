from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_kwargs

if TYPE_CHECKING:
    from app.models.user import User


class PortfolioType(str, Enum):
    STOCKS = "stocks"
    REAL_ESTATE = "real_estate"
    MIXED = "mixed"
    WATCHLIST = "watchlist"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"


portfolio_type_enum = SqlEnum(PortfolioType, name="portfolio_type", **enum_kwargs(PortfolioType))
transaction_type_enum = SqlEnum(TransactionType, name="transaction_type", **enum_kwargs(TransactionType))


class Portfolio(BaseModel):
    __tablename__ = "portfolios"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_type: Mapped[PortfolioType] = mapped_column(portfolio_type_enum, default=PortfolioType.MIXED, nullable=False)

    base_currency: Mapped[str] = mapped_column(String(3), default="AED", nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    total_value_aed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost_aed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_return_aed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_return_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="portfolios")
    holdings: Mapped[list["PortfolioHolding"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    performance_snapshots: Mapped[list["PortfolioPerformance"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(BaseModel):
    __tablename__ = "portfolio_holdings"

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    asset_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    average_cost: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    unrealized_gain_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_gain_loss_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_gain_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_dividends: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(back_populates="holding")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_holding_symbol"),
    )


class PortfolioTransaction(BaseModel):
    __tablename__ = "portfolio_transactions"

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    holding_id: Mapped[int | None] = mapped_column(ForeignKey("portfolio_holdings.id", ondelete="SET NULL"), nullable=True)

    transaction_type: Mapped[TransactionType] = mapped_column(transaction_type_enum, nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    fees: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="transactions")
    holding: Mapped["PortfolioHolding | None"] = relationship(back_populates="transactions")


class PortfolioPerformance(BaseModel):
    __tablename__ = "portfolio_performance"

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_return_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    holdings_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sector_allocation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    asset_allocation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="performance_snapshots")

    __table_args__ = (
        Index("idx_portfolio_snapshot", "portfolio_id", "snapshot_date"),
    )


class Watchlist(BaseModel):
    __tablename__ = "watchlists"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alert_on_change: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_threshold_percent: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="watchlists")
    items: Mapped[list["WatchlistItem"]] = relationship(back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(BaseModel):
    __tablename__ = "watchlist_items"

    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    asset_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_buy_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_sell_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    added_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )


class InvestmentRecommendation(BaseModel):
    __tablename__ = "investment_recommendations"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recommendation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    investment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_factors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_horizon_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    price_at_recommendation: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    closed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="investment_recommendations")
