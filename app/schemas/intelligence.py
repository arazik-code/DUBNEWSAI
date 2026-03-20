from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MarketHealthResponse(BaseModel):
    overall_score: float
    components: dict[str, float]
    grade: str
    trend: str


class RSIResponse(BaseModel):
    current: float
    signal: str
    trend: str


class MACDResponse(BaseModel):
    value: float
    signal_line: float
    histogram: float
    signal: str
    strength: float


class RateOfChangeResponse(BaseModel):
    ten_day: float
    thirty_day: float
    acceleration: str


class MomentumIndicatorsResponse(BaseModel):
    rsi: RSIResponse
    macd: MACDResponse
    rate_of_change: RateOfChangeResponse


class SymbolReturnResponse(BaseModel):
    symbol: str
    name: str
    return_30d: float


class SectorPerformanceItem(BaseModel):
    sector: str
    return_30d: float
    volatility: float
    sharpe_ratio: float
    avg_volume: int
    stock_count: int
    top_performers: list[SymbolReturnResponse]


class SectorPerformanceResponse(BaseModel):
    sectors: list[SectorPerformanceItem]
    rankings: dict[str, str | None]


class VolatilityMetricsResponse(BaseModel):
    historical_volatility: float
    volatility_30d: float
    volatility_90d: float
    regime: str
    downside_deviation: float
    max_drawdown: float
    var_95: float
    cvar_95: float


class CorrelationPairResponse(BaseModel):
    asset_1: str
    asset_2: str
    correlation: float


class CorrelationMatrixResponse(BaseModel):
    matrix: dict[str, dict[str, float]]
    high_correlations: list[CorrelationPairResponse]
    average_correlation: float


class KeyDriverResponse(BaseModel):
    factor: str
    impact: str
    strength: float | None = None
    description: str
    current_value: float | str | None = None
    trend: str | None = None


class RiskFactorResponse(BaseModel):
    category: str
    severity: str
    description: str
    mitigation: str


class OpportunityResponse(BaseModel):
    type: str
    symbol: str | None = None
    indicator: str
    value: float | None = None
    rationale: str
    confidence: str


class BenchmarkSnapshotResponse(BaseModel):
    symbol: str
    name: str
    price: float
    change_percent: float
    region: str | None = None
    asset_class: str | None = None
    exchange: str | None = None


class ExecutiveSummaryResponse(BaseModel):
    headline: str
    narrative: str
    focus_areas: list[str]


class MarketIntelligenceResponse(BaseModel):
    market_health_score: MarketHealthResponse
    momentum_indicators: MomentumIndicatorsResponse
    sector_performance: SectorPerformanceResponse
    volatility_analysis: VolatilityMetricsResponse
    correlation_matrix: CorrelationMatrixResponse
    key_drivers: list[KeyDriverResponse]
    risk_factors: list[RiskFactorResponse]
    opportunities: list[OpportunityResponse]
    benchmark_snapshots: list[BenchmarkSnapshotResponse]
    executive_summary: ExecutiveSummaryResponse
    timestamp: datetime


class PropertyValuationRequest(BaseModel):
    area_sqft: float
    bedrooms: int
    location: str
    property_type: str
    year_built: int
    amenities: list[str] = []


class ComparablePropertyResponse(BaseModel):
    title: str
    location: str
    property_type: str
    bedrooms: int
    area_sqft: float
    estimated_price_aed: float
    price_per_sqft: float
    similarity_score: float


class PropertyValuationResponse(BaseModel):
    estimated_value_aed: float
    confidence_interval: dict[str, float]
    price_per_sqft: float
    market_trend: float
    comparables: list[ComparablePropertyResponse]
    value_drivers: list[dict[str, str | float]]
    valuation_date: datetime
    narrative: str


class ROIRequest(BaseModel):
    purchase_price: float
    rental_income_monthly: float
    expenses_monthly: float
    appreciation_rate: float = 0.05


class ROIProjectionResponse(BaseModel):
    year: int
    property_value: float
    cumulative_rental_income: float
    total_return: float
    roi_percent: float


class ROIResponse(BaseModel):
    cap_rate: float
    cash_on_cash_return: float
    annual_net_income: float
    payback_period_years: float | None = None
    projections: list[ROIProjectionResponse]
    investment_grade: str


class ComparativeAnalysisRequest(BaseModel):
    location: str
    property_type: str
    bedrooms: int
    area_sqft: float
    year_built: int
    radius_km: float = 2.0


class MarketStatisticsResponse(BaseModel):
    average_price: float
    median_price: float
    price_range: tuple[float, float]
    average_price_per_sqft: float
    median_price_per_sqft: float
    total_sales: int
    days_on_market_avg: float


class ComparativeAnalysisResponse(BaseModel):
    recent_sales: list[ComparablePropertyResponse]
    market_statistics: MarketStatisticsResponse | None = None
    market_activity: str
    recommendation: str

