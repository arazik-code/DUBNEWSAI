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


class MarketBoardHealthResponse(BaseModel):
    board: str
    status: str
    total_rows: int
    live_rows: int
    fallback_rows: int
    last_updated: datetime | None = None
    providers: list[str] = []


class MarketCoverageSnapshotResponse(BaseModel):
    tracked_symbols: int
    live_symbols: int
    fallback_symbols: int
    fx_pairs: int
    macro_indicators: int
    provider_count: int


class ProviderUtilizationResponse(BaseModel):
    provider: str
    type: str
    health: str
    circuit_state: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None


class MarketInsightHighlightResponse(BaseModel):
    title: str
    value: str
    context: str


class MarketBriefResponse(BaseModel):
    headline: str
    narrative: str
    focus_areas: list[str] = []
    confidence: str


class MarketCoverageAlertResponse(BaseModel):
    board: str
    severity: str
    message: str
    action: str
    affected_symbols: list[str] = []


class MarketProviderMixResponse(BaseModel):
    active_count: int
    dormant_count: int
    top_contributors: list[str] = []
    dormant_providers: list[str] = []


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
    board_health: list[MarketBoardHealthResponse] = []
    coverage_snapshot: MarketCoverageSnapshotResponse | None = None
    provider_utilization: list[ProviderUtilizationResponse] = []
    provider_mix: MarketProviderMixResponse | None = None
    intelligence_highlights: list[MarketInsightHighlightResponse] = []
    market_brief: MarketBriefResponse | None = None
    coverage_alerts: list[MarketCoverageAlertResponse] = []
