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
