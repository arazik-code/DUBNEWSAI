from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.market_data import MarketType, StockExchange


class MarketDataResponse(BaseModel):
    id: int
    symbol: str
    name: str
    market_type: MarketType
    exchange: StockExchange | None
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float | None
    data_timestamp: datetime
    is_live_data: bool = True
    data_source: str = "market_data"

    model_config = ConfigDict(from_attributes=True)


class CurrencyRateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class EconomicIndicatorResponse(BaseModel):
    indicator_name: str
    indicator_code: str
    value: float
    unit: str | None
    country: str
    period: str | None
    timestamp: datetime
    source: str | None

    model_config = ConfigDict(from_attributes=True)


class MarketOverview(BaseModel):
    stocks: list[MarketDataResponse]
    indices: list[MarketDataResponse]
    currencies: list[CurrencyRateResponse]
    economic_indicators: list[EconomicIndicatorResponse]
    real_estate_companies: list[MarketDataResponse]
