from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_kwargs

if TYPE_CHECKING:
    from app.models.sources import MarketDataSource


class MarketType(str, Enum):
    STOCK = "stock"
    INDEX = "index"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    CRYPTO = "crypto"


class StockExchange(str, Enum):
    DFM = "dfm"
    ADX = "adx"
    NASDAQ = "nasdaq"
    NYSE = "nyse"


market_type_enum = SqlEnum(MarketType, name="market_type", **enum_kwargs(MarketType))
stock_exchange_enum = SqlEnum(StockExchange, name="stock_exchange", **enum_kwargs(StockExchange))


class MarketData(BaseModel):
    __tablename__ = "market_data"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(market_type_enum, nullable=False, index=True)
    exchange: Mapped[StockExchange | None] = mapped_column(stock_exchange_enum, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_close: Mapped[float | None] = mapped_column(Float, nullable=True)

    volume: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)

    change: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    change_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="AED", nullable=False)
    primary_provider: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    pe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    dividend_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    week_52_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    week_52_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    sources: Mapped[list["MarketDataSource"]] = relationship(
        back_populates="market_data",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_symbol_timestamp", "symbol", "data_timestamp"),
        Index("idx_type_timestamp", "market_type", "data_timestamp"),
    )


class CurrencyRate(BaseModel):
    __tablename__ = "currency_rates"

    from_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_currency_pair", "from_currency", "to_currency", "timestamp"),
    )


class EconomicIndicator(BaseModel):
    __tablename__ = "economic_indicators"

    indicator_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    indicator_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(3), default="UAE", nullable=False)
    period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class WatchlistSymbol(BaseModel):
    __tablename__ = "watchlist_symbols"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(market_type_enum, nullable=False)
    exchange: Mapped[StockExchange | None] = mapped_column(stock_exchange_enum, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_real_estate_company: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
