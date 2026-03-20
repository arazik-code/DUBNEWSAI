export interface MarketStock {
  id: number
  symbol: string
  name: string
  price: number
  open_price?: number | null
  high_price?: number | null
  low_price?: number | null
  previous_close?: number | null
  change: number
  change_percent: number
  volume: number
  market_type: string
  exchange?: string | null
  market_cap?: number | null
  currency: string
  primary_provider?: string | null
  data_quality_score?: number | null
  confidence_level?: string | null
  asset_class?: string | null
  region?: string | null
  data_timestamp: string
  is_live_data?: boolean
  data_source?: string
}

export interface CurrencyRate {
  from_currency: string
  to_currency: string
  rate: number
  timestamp: string
}

export interface EconomicIndicator {
  indicator_name: string
  indicator_code: string
  value: number
  unit?: string | null
  country: string
  period?: string | null
  timestamp: string
  source?: string | null
}

export interface WeatherSnapshot {
  location_name: string
  latitude: number
  longitude: number
  temperature_c: number
  apparent_temperature_c?: number | null
  humidity_percent?: number | null
  wind_speed_kph?: number | null
  weather_code?: number | null
  weather_summary: string
  observed_at: string
  source: string
}

export interface MarketOverviewResponse {
  stocks: MarketStock[]
  indices: MarketStock[]
  global_real_estate: MarketStock[]
  commodities: MarketStock[]
  currencies: CurrencyRate[]
  economic_indicators: EconomicIndicator[]
  real_estate_companies: MarketStock[]
  weather?: WeatherSnapshot | null
  market_status?: Record<string, string> | null
}

export interface MarketHealth {
  overall_score: number
  components: Record<string, number>
  grade: string
  trend: string
}

export interface MomentumIndicators {
  rsi: {
    current: number
    signal: string
    trend: string
  }
  macd: {
    value: number
    signal_line: number
    histogram: number
    signal: string
    strength: number
  }
  rate_of_change: {
    ten_day: number
    thirty_day: number
    acceleration: string
  }
}

export interface SectorPerformer {
  symbol: string
  name: string
  return_30d: number
}

export interface SectorPerformanceItem {
  sector: string
  return_30d: number
  volatility: number
  sharpe_ratio: number
  avg_volume: number
  stock_count: number
  top_performers: SectorPerformer[]
}

export interface MarketIntelligenceResponse {
  market_health_score: MarketHealth
  momentum_indicators: MomentumIndicators
  sector_performance: {
    sectors: SectorPerformanceItem[]
    rankings: Record<string, string | null>
  }
  volatility_analysis: {
    historical_volatility: number
    volatility_30d: number
    volatility_90d: number
    regime: string
    downside_deviation: number
    max_drawdown: number
    var_95: number
    cvar_95: number
  }
  correlation_matrix: {
    matrix: Record<string, Record<string, number>>
    high_correlations: { asset_1: string; asset_2: string; correlation: number }[]
    average_correlation: number
  }
  key_drivers: {
    factor: string
    impact: string
    strength?: number | null
    description: string
    current_value?: number | string | null
    trend?: string | null
  }[]
  risk_factors: {
    category: string
    severity: string
    description: string
    mitigation: string
  }[]
  opportunities: {
    type: string
    symbol?: string | null
    indicator: string
    value?: number | null
    rationale: string
    confidence: string
  }[]
  benchmark_snapshots: {
    symbol: string
    name: string
    price: number
    change_percent: number
    region?: string | null
    asset_class?: string | null
    exchange?: string | null
  }[]
  executive_summary: {
    headline: string
    narrative: string
    focus_areas: string[]
  }
  timestamp: string
}

export interface PropertyValuationRequest {
  area_sqft: number
  bedrooms: number
  location: string
  property_type: string
  year_built: number
  amenities: string[]
}

export interface PropertyComparable {
  title: string
  location: string
  property_type: string
  bedrooms: number
  area_sqft: number
  estimated_price_aed: number
  price_per_sqft: number
  similarity_score: number
}

export interface PropertyValuationResponse {
  estimated_value_aed: number
  confidence_interval: {
    lower: number
    upper: number
  }
  price_per_sqft: number
  market_trend: number
  comparables: PropertyComparable[]
  value_drivers: {
    label: string
    value: string | number
    context: string
  }[]
  valuation_date: string
  narrative: string
}

export interface ROIRequest {
  purchase_price: number
  rental_income_monthly: number
  expenses_monthly: number
  appreciation_rate: number
}

export interface ROIResponse {
  cap_rate: number
  cash_on_cash_return: number
  annual_net_income: number
  payback_period_years?: number | null
  projections: {
    year: number
    property_value: number
    cumulative_rental_income: number
    total_return: number
    roi_percent: number
  }[]
  investment_grade: string
}

export interface ComparativeAnalysisRequest {
  location: string
  property_type: string
  bedrooms: number
  area_sqft: number
  year_built: number
  radius_km: number
}

export interface ComparativeAnalysisResponse {
  recent_sales: PropertyComparable[]
  market_statistics?: {
    average_price: number
    median_price: number
    price_range: [number, number]
    average_price_per_sqft: number
    median_price_per_sqft: number
    total_sales: number
    days_on_market_avg: number
  } | null
  market_activity: string
  recommendation: string
}
