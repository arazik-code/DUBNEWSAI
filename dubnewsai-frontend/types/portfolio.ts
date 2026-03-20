export interface PortfolioHolding {
  id: number
  symbol: string
  asset_type?: string | null
  asset_name?: string | null
  quantity: number
  average_cost: number
  current_price?: number | null
  current_value?: number | null
  unrealized_gain_loss?: number | null
  unrealized_gain_loss_percent?: number | null
  realized_gain_loss?: number | null
  total_dividends: number
  purchase_date?: string | null
}

export interface Portfolio {
  id: number
  name: string
  description?: string | null
  portfolio_type: string
  base_currency: string
  is_public: boolean
  auto_update: boolean
  total_value_aed: number
  total_cost_aed: number
  total_return_aed: number
  total_return_percent: number
  last_updated?: string | null
  holdings: PortfolioHolding[]
}

export interface PortfolioAnalytics {
  overview: Record<string, number>
  allocation: {
    by_asset: Record<string, { value: number; percent: number; quantity: number }>
    by_sector: Record<string, number>
    concentration: {
      herfindahl_index: number
      top_5_concentration: number
      diversification_score: number
    }
  }
  performance: Record<string, number>
  risk_metrics: Record<string, number | string>
  top_performers: { symbol: string; return_percent: number; return_amount: number; current_value: number }[]
  bottom_performers: { symbol: string; return_percent: number; return_amount: number; current_value: number }[]
  dividend_income: {
    total_dividends: number
    dividend_yield: number
    annualized_income: number
  }
}

export interface WatchlistItem {
  id: number
  symbol: string
  asset_type?: string | null
  asset_name?: string | null
  target_buy_price?: number | null
  target_sell_price?: number | null
  notes?: string | null
  tags?: string[] | null
  added_price?: number | null
  current_price?: number | null
  price_change_percent?: number | null
}

export interface Watchlist {
  id: number
  name: string
  description?: string | null
  alert_on_change: boolean
  change_threshold_percent: number
  items: WatchlistItem[]
}

export interface InvestmentScore {
  symbol: string
  overall_score: number
  component_scores: Record<string, number>
  recommendation: string
  confidence: string
  rationale: string
  key_factors: string[]
  risks: string[]
  target_price: number
  stop_loss: number
  time_horizon: string
  generated_at: string
}
