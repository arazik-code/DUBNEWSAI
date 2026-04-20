export type UserRole = "admin" | "premium" | "user" | string;

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  role: UserRole;
  created_at: string;
};

export type UserSession = {
  accessToken: string;
  refreshToken: string;
  user: User | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type FeatureAccessItem = {
  feature_key: string;
  label: string;
  description: string | null;
  category: string;
  public_access: boolean;
  grantable: boolean;
  has_access: boolean;
};

export type MobileArticleCard = {
  id: number;
  title: string;
  description: string | null;
  source_name: string | null;
  category: string;
  sentiment: string;
  published_at: string;
  image_url: string | null;
  relevance_score: number;
};

export type MobileMarketCard = {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  currency: string;
  exchange: string | null;
  market_type: string | null;
};

export type MobileNotificationCard = {
  id: number;
  title: string;
  message: string;
  priority: string;
  created_at: string;
  is_read: boolean;
};

export type MobileWorkspaceSummary = {
  user: User;
  enabled_features: string[];
  portfolios: {
    portfolio_count: number;
    watchlist_count: number;
    total_value_aed: number;
    total_return_percent: number;
    watch_items: number;
    top_holdings: {
      symbol: string;
      asset_name: string | null;
      current_value: number;
      return_percent: number;
    }[];
  } | null;
  alerts: {
    summary: Record<string, number>;
    recent_triggers: Array<Record<string, unknown>>;
    templates: Array<Record<string, unknown>>;
  } | null;
  notifications: {
    unread_count: number;
    latest: MobileNotificationCard[];
  };
  teams_count: number;
  competitor_spotlight: {
    id: number;
    name: string;
    ticker_symbol: string | null;
    market_share_percent: number | null;
    threat_level: string | null;
    strategic_note: string | null;
  } | null;
};

export type MobileBootstrapResponse = {
  app_name: string;
  app_version: string;
  feature_access: FeatureAccessItem[];
  hero_article: MobileArticleCard | null;
  featured_articles: MobileArticleCard[];
  trending_articles: MobileArticleCard[];
  market_pulse: {
    market_status: Record<string, string> | null;
    movers: MobileMarketCard[];
    real_estate_leaders: MobileMarketCard[];
    weather: {
      location_name: string;
      temperature_c: number;
      weather_summary: string;
      observed_at: string;
    } | null;
    trend_prediction: Record<string, unknown> | null;
  };
  prediction_universe: {
    symbols: Array<{
      symbol: string;
      canonical_symbol: string;
      name: string;
      exchange: string | null;
      sector: string | null;
      price: number;
      change_percent: number;
    }>;
    locations: Array<{
      name: string;
      price_per_sqft: number;
      trend_percent: number;
      supported_types: string[];
    }>;
    property_types: string[];
  };
  property_options: {
    locations: Array<{
      name: string;
      price_per_sqft: number;
      trend_percent: number;
      supported_types: string[];
    }>;
    property_types: string[];
    amenities?: string[];
  };
  workspace_summary: MobileWorkspaceSummary | null;
};

export type NewsArticle = {
  id: number;
  title: string;
  description: string | null;
  content: string | null;
  url: string;
  source: string;
  source_name: string | null;
  author: string | null;
  category: string;
  sentiment: string;
  sentiment_score: number;
  keywords: string[] | null;
  entities: Record<string, string[]> | null;
  published_at: string;
  primary_provider: string | null;
  duplicate_count: number;
  quality_score: number;
  image_url: string | null;
  video_url: string | null;
  view_count: number;
  relevance_score: number;
  is_featured: boolean;
  is_published: boolean;
  enrichment_status: string | null;
  enriched_at: string | null;
  created_at: string;
  updated_at: string;
};

export type NewsListResponse = {
  total: number;
  page: number;
  page_size: number;
  articles: NewsArticle[];
};

export type MarketData = {
  id: number;
  symbol: string;
  name: string;
  market_type: string;
  exchange: string | null;
  price: number;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  previous_close: number | null;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number | null;
  currency: string;
  primary_provider?: string | null;
  data_quality_score?: number | null;
  asset_class?: string | null;
  region?: string | null;
  data_timestamp: string;
  is_live_data?: boolean;
  data_source?: string | null;
};

export type MarketOverview = {
  stocks: MarketData[];
  indices: MarketData[];
  global_real_estate: MarketData[];
  commodities: MarketData[];
  currencies: Array<{ from_currency: string; to_currency: string; rate: number; timestamp: string }>;
  economic_indicators: Array<{ indicator_name: string; indicator_code: string; value: number; unit: string | null; country: string; period: string | null; timestamp: string; source: string | null }>;
  real_estate_companies: MarketData[];
  weather: {
    location_name: string;
    temperature_c: number;
    apparent_temperature_c: number | null;
    humidity_percent: number | null;
    wind_speed_kph: number | null;
    weather_summary: string;
    observed_at: string;
  } | null;
  market_status: Record<string, string> | null;
  board_health?: Array<{
    board: string;
    status: string;
    total_rows: number;
    live_rows: number;
    fallback_rows: number;
    last_updated: string | null;
    providers: string[];
  }>;
  coverage_snapshot?: {
    tracked_symbols: number;
    live_symbols: number;
    fallback_symbols: number;
    fx_pairs: number;
    macro_indicators: number;
    provider_count: number;
  };
  provider_utilization?: Array<{
    provider: string;
    type: string;
    circuit_state: string;
    total_calls: number;
    successful_calls: number;
    failed_calls: number;
    last_success_at?: string | null;
  }>;
  provider_mix?: {
    active_count: number;
    dormant_count: number;
    top_contributors: string[];
    dormant_providers: string[];
  };
  market_brief?: {
    headline: string;
    narrative: string;
    focus_areas: string[];
    confidence: string;
  };
  coverage_alerts?: Array<{
    board: string;
    severity: string;
    message: string;
    action: string;
    affected_symbols: string[];
  }>;
};

export type PricePrediction = {
  symbol: string;
  current_price: number;
  forecast_horizon_days: number;
  prediction: {
    target_price: number;
    expected_return_percent: number;
    confidence_interval: {
      lower: number;
      upper: number;
    };
  };
  trend: {
    direction: string;
    strength: number;
    slope: number;
  };
  forecast_series: Array<{
    days_ahead: number;
    predicted_price: number;
    upper_bound: number;
    lower_bound: number;
  }>;
  model_info: {
    method: string;
    r_squared: number;
    data_points: number;
    data_source: string;
  };
  generated_at: string;
};

export type MarketTrendPrediction = {
  region: string;
  prediction: string;
  confidence: string;
  trend_score: number;
  factors: Array<{ factor: string; contribution: number; description: string }>;
  recommendation: string;
  timeframe: string;
  generated_at: string;
};

export type PropertyTrendPrediction = {
  location: string;
  property_type: string;
  current_avg_price: number;
  yoy_growth_percent: number;
  forecast_12m: {
    predicted_price: number;
    expected_appreciation: number;
    trend: string;
  };
  monthly_forecast: Array<{ month: number; predicted_price: number }>;
  confidence: string;
  data_quality: {
    r_squared: number;
    data_points: number;
  };
  generated_at: string;
};

export type PropertyPreset = {
  location: string;
  property_type: string;
  valuation_defaults: {
    location: string;
    property_type: string;
    area_sqft: number;
    bedrooms: number;
    year_built: number;
    amenities: string[];
  };
  roi_defaults: {
    purchase_price: number;
    rental_income_monthly: number;
    expenses_monthly: number;
    appreciation_rate: number;
  };
  market_context: {
    baseline_price_per_sqft: number;
    market_trend_percent: number;
    supported_types: string[];
  };
};

export type PropertyEstimate = {
  estimated_value_aed: number;
  price_per_sqft: number;
  confidence_interval: {
    low: number;
    high: number;
  };
  market_trend: number;
  comparables: Array<Record<string, unknown>>;
  value_drivers: Array<Record<string, unknown>>;
  valuation_date: string;
  narrative: string;
};

export type ROIResult = {
  gross_yield_percent: number;
  net_yield_percent: number;
  annual_cash_flow: number;
  five_year_projection: number;
  payback_period_years: number;
};

export type PortfolioHolding = {
  id: number;
  symbol: string;
  asset_type: string | null;
  asset_name: string | null;
  quantity: number;
  average_cost: number;
  current_price: number | null;
  current_value: number | null;
  unrealized_gain_loss: number | null;
  unrealized_gain_loss_percent: number | null;
  realized_gain_loss: number | null;
  total_dividends: number;
  purchase_date: string | null;
};

export type Portfolio = {
  id: number;
  name: string;
  description: string | null;
  portfolio_type: string;
  base_currency: string;
  is_public: boolean;
  auto_update: boolean;
  total_value_aed: number;
  total_cost_aed: number;
  total_return_aed: number;
  total_return_percent: number;
  last_updated: string | null;
  holdings: PortfolioHolding[];
};

export type Watchlist = {
  id: number;
  name: string;
  description: string | null;
  alert_on_change: boolean;
  change_threshold_percent: number;
  items: Array<{
    id: number;
    symbol: string;
    asset_type: string | null;
    asset_name: string | null;
    target_buy_price: number | null;
    target_sell_price: number | null;
    notes: string | null;
    tags: string[] | null;
    added_price: number | null;
    current_price: number | null;
    price_change_percent: number | null;
  }>;
};

export type AssetCatalogItem = {
  symbol: string;
  canonical_symbol: string;
  name: string;
  sector: string;
  price: number;
  change_percent: number;
  exchange: string | null;
  currency: string;
};

export type PortfolioAnalytics = {
  overview: Record<string, number>;
  allocation: Record<string, unknown>;
  performance: Record<string, number>;
  risk_metrics: Record<string, number | string>;
  top_performers: Array<Record<string, number | string>>;
  bottom_performers: Array<Record<string, number | string>>;
  dividend_income: Record<string, number>;
};

export type Alert = {
  id: number;
  name: string;
  alert_type: string;
  status: string;
  symbol: string | null;
  keywords: string[] | null;
  threshold_value: number | null;
  category: string | null;
  frequency: string;
  trigger_count: number;
  last_triggered_at: string | null;
  is_active: boolean;
  created_at: string;
};

export type AlertIntelligence = {
  summary: Record<string, number>;
  templates: Array<Record<string, unknown>>;
  recent_triggers: Array<Record<string, unknown>>;
};

export type NotificationItem = {
  id: number;
  type: string;
  priority: string;
  title: string;
  message: string;
  is_read: boolean;
  article_id: number | null;
  market_symbol: string | null;
  created_at: string;
};

export type Competitor = {
  id: number;
  name: string;
  industry: string | null;
  sector: string | null;
  ticker_symbol: string | null;
  market_cap: number | null;
  revenue_growth_rate: number | null;
  market_share_percent: number | null;
  description: string | null;
  last_analyzed: string | null;
};

export type CompetitorCatalogItem = {
  name: string;
  industry: string | null;
  sector: string | null;
  ticker_symbol: string | null;
  market_share_percent: number | null;
  revenue_growth_rate: number | null;
  market_cap: number | null;
  headquarters: string | null;
  tags: string[] | null;
  description: string | null;
  tracked: boolean;
};

export type CompetitorAnalysis = {
  competitor: Record<string, unknown>;
  swot_analysis: Record<string, unknown>;
  news_intelligence: Record<string, unknown>;
  market_positioning: Record<string, unknown>;
  product_comparison: Record<string, unknown>;
  pricing_analysis: Record<string, unknown>;
  performance_trends: Record<string, unknown>;
  threat_assessment: Record<string, unknown>;
  strategic_insights: Array<Record<string, unknown>>;
};

export type ExecutiveDashboard = {
  summary: {
    period: string;
    key_points: Array<{ category: string; status: string; message: string }>;
    overall_sentiment: string;
    action_items: string[];
  };
  kpis: Record<string, unknown>;
  market_overview: Record<string, unknown>;
  competitive_landscape: Record<string, unknown>;
  strategic_priorities: Array<Record<string, unknown>>;
  risk_dashboard: Record<string, unknown>;
  opportunity_pipeline: Array<Record<string, unknown>>;
  generated_at: string;
};

export type Team = {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  is_active: boolean;
  max_members: number;
  shared_portfolios: boolean;
  shared_watchlists: boolean;
  shared_insights: boolean;
  created_at: string;
  updated_at: string;
};
