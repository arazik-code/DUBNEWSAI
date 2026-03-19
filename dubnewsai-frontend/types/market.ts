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
