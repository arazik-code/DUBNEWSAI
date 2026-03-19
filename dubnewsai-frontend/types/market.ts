export interface MarketStock {
  id: number
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume: number
  market_type: string
  exchange?: string | null
  market_cap?: number | null
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

export interface MarketOverviewResponse {
  stocks: MarketStock[]
  indices: MarketStock[]
  currencies: CurrencyRate[]
  economic_indicators: EconomicIndicator[]
  real_estate_companies: MarketStock[]
}
