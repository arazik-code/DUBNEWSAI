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
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    previous_close: float | None = None
    change: float
    change_percent: float
    volume: int
    market_cap: float | None
    currency: str
    primary_provider: str | None = None
    data_quality_score: float | None = None
    confidence_level: str | None = None
    asset_class: str | None = None
    region: str | None = None
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


class WeatherSnapshotResponse(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    temperature_c: float
    apparent_temperature_c: float | None
    humidity_percent: int | None
    wind_speed_kph: float | None
    weather_code: int | None
    weather_summary: str
    observed_at: datetime
    source: str


class MarketOverview(BaseModel):
    stocks: list[MarketDataResponse]
    indices: list[MarketDataResponse]
    global_real_estate: list[MarketDataResponse] = []
    commodities: list[MarketDataResponse] = []
    currencies: list[CurrencyRateResponse]
    economic_indicators: list[EconomicIndicatorResponse]
    real_estate_companies: list[MarketDataResponse]
    weather: WeatherSnapshotResponse | None = None
    market_status: dict[str, str] | None = None
