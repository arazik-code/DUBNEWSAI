export interface Competitor {
  id: number
  name: string
  official_name?: string | null
  industry?: string | null
  sector?: string | null
  headquarters?: string | null
  ticker_symbol?: string | null
  website?: string | null
  description?: string | null
  founded_year?: number | null
  employee_count?: number | null
  market_cap?: number | null
  revenue_annual?: number | null
  revenue_growth_rate?: number | null
  profit_margin?: number | null
  market_share_percent?: number | null
  competitive_strength_score?: number | null
  is_active: boolean
  last_analyzed?: string | null
  tags?: string[] | null
  created_at: string
  updated_at: string
}

export interface CompetitorAnalysis {
  competitor: Record<string, unknown>
  swot_analysis: {
    strengths: { category: string; description: string; impact: string }[]
    weaknesses: { category: string; description: string; impact: string }[]
    opportunities: { category: string; description: string; impact: string }[]
    threats: { category: string; description: string; impact: string }[]
    competitive_position: string
    threat_level: string
  }
  news_intelligence: {
    total_mentions: number
    average_sentiment: number
    sentiment_label: string
    coverage_trend: string
    mention_breakdown: Record<string, number>
    top_stories: { title: string; source: string; published_at: string; sentiment?: number | null; type?: string | null }[]
  }
  market_positioning: Record<string, string | number | null>
  product_comparison: {
    product_count: number
    avg_price?: number | null
    pricing_strategy: string
    products: {
      name: string
      category?: string | null
      price?: number | null
      pricing_model?: string | null
      key_features_count: number
      market_reception?: string | null
      estimated_users?: number | null
      our_advantage?: string[] | null
      their_advantage?: string[] | null
    }[]
  }
  pricing_analysis: Record<string, string | number | string[] | [number, number] | null>
  performance_trends: Record<string, string | number | boolean>
  threat_assessment: {
    threat_level: string
    threat_score: number
    threat_factors: { factor: string; severity: string; description: string }[]
    recommended_actions: string[]
  }
  strategic_insights: { type: string; priority: string; title: string; description: string; recommendation: string; timeframe: string }[]
}

export interface PricePrediction {
  symbol: string
  current_price: number
  forecast_horizon_days: number
  prediction: {
    target_price: number
    expected_return_percent: number
    confidence_interval: {
      lower: number
      upper: number
    }
  }
  trend: {
    direction: string
    strength: number
    slope: number
  }
  forecast_series: { days_ahead: number; predicted_price: number; upper_bound: number; lower_bound: number }[]
  model_info: {
    method: string
    r_squared: number
    data_points: number
  }
  generated_at: string
}

export interface MarketTrendPrediction {
  region: string
  prediction: string
  confidence: string
  trend_score: number
  factors: { factor: string; contribution: number; description: string }[]
  recommendation: string
  timeframe: string
  generated_at: string
}

export interface PropertyTrendPrediction {
  location: string
  property_type: string
  current_avg_price: number
  yoy_growth_percent: number
  forecast_12m: {
    predicted_price: number
    expected_appreciation: number
    trend: string
  }
  monthly_forecast: { month: number; predicted_price: number }[]
  confidence: string
  data_quality: {
    r_squared: number
    data_points: number
  }
  generated_at: string
}

export interface ExecutiveDashboard {
  summary: {
    period: string
    key_points: { category: string; status: string; message: string }[]
    overall_sentiment: string
    action_items: string[]
  }
  kpis: {
    market_health_score: number
    portfolio_performance: { total_return: number; return_percent: number; vs_benchmark: number; sharpe_ratio: number }
    competitive_position: { market_share_trend: string; competitive_wins: number; win_rate_percent: number }
    operational_metrics: { data_quality_score: number; system_uptime: number; user_engagement: string }
    risk_metrics: { overall_risk_level: string; top_risks_count: number; mitigation_status: string }
  }
  market_overview: {
    headline: string
    key_insights: { title: string; value: string; trend: string; context: string }[]
    sector_performance: { sector: string; performance: string; change: number }[]
    economic_indicators: { gdp_growth: number; inflation: number; tourism_index: number }
  }
  competitive_landscape: {
    market_leaders: { name: string; market_share?: number | null; threat_level: string; recent_activity: string }[]
    competitive_dynamics: { market_concentration: string; new_entrants: number; competitive_intensity: string }
    our_position: { relative_strength: string; differentiation: string[]; growth_opportunity: string }
  }
  strategic_priorities: {
    priority: number
    title: string
    category: string
    rationale: string
    key_actions: string[]
    expected_impact: string
    timeframe: string
    owner: string
  }[]
  risk_dashboard: {
    overall_risk_rating: string
    risk_trend: string
    top_risks: { category: string; severity: string; description: string; probability: string; impact: string; mitigation: string; owner: string }[]
    risk_metrics: { risks_identified: number; risks_mitigated: number; risks_monitoring: number; new_risks_this_period: number }
  }
  opportunity_pipeline: {
    opportunity: string
    category: string
    potential_value: string
    probability: string
    investment_required: string
    timeline: string
    key_requirements: string[]
    status: string
  }[]
  generated_at: string
}

export interface Team {
  id: number
  name: string
  description?: string | null
  owner_id: number
  is_active: boolean
  max_members: number
  shared_portfolios: boolean
  shared_watchlists: boolean
  shared_insights: boolean
  created_at: string
  updated_at: string
}

export interface TeamActivity {
  id: number
  activity_type: string
  description?: string | null
  metadata: Record<string, unknown>
  created_at: string
  user?: { id: number; full_name?: string | null; email: string } | null
}

export interface ApiKeyRecord {
  id: number
  name: string
  is_active: boolean
  rate_limit_per_hour: number
  total_requests: number
  last_used_at?: string | null
  scopes?: string[] | null
  created_at: string
  updated_at: string
}

export interface ApiKeyCreated extends ApiKeyRecord {
  plaintext_key: string
}

export interface WhiteLabelConfig {
  id: number
  company_name: string
  logo_url?: string | null
  primary_color?: string | null
  secondary_color?: string | null
  custom_domain?: string | null
  subdomain?: string | null
  enabled_features?: string[] | null
  api_enabled: boolean
  api_rate_limit: number
  is_active: boolean
  created_at: string
  updated_at: string
}
