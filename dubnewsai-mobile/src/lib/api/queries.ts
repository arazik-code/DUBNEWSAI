import { apiRequest } from "./client";
import type {
  Alert,
  AlertIntelligence,
  AssetCatalogItem,
  Competitor,
  CompetitorCatalogItem,
  CompetitorAnalysis,
  ExecutiveDashboard,
  FeatureAccessItem,
  MarketData,
  MarketOverview,
  MarketTrendPrediction,
  MobileBootstrapResponse,
  MobileWorkspaceSummary,
  NewsArticle,
  NewsListResponse,
  NotificationItem,
  Portfolio,
  PortfolioAnalytics,
  PricePrediction,
  PropertyEstimate,
  PropertyPreset,
  PropertyTrendPrediction,
  Team,
  Watchlist,
} from "./types";
import { appConfig } from "../config";
import { useAuthStore } from "../state/auth-store";

type NewsFilters = {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
};

function mapMarketCard(item: MarketData): MobileBootstrapResponse["market_pulse"]["movers"][number] {
  return {
    symbol: item.symbol,
    name: item.name,
    price: item.price,
    change_percent: item.change_percent,
    currency: item.currency,
    exchange: item.exchange,
    market_type: item.market_type,
  };
}

function buildPortfolioSnapshot(portfolios: Portfolio[], watchlists: Watchlist[]) {
  const holdings = portfolios.flatMap((portfolio) => portfolio.holdings ?? []);
  holdings.sort((left, right) => (right.current_value ?? 0) - (left.current_value ?? 0));

  const totalValue = portfolios.reduce((sum, portfolio) => sum + (portfolio.total_value_aed ?? 0), 0);
  const totalCost = portfolios.reduce((sum, portfolio) => sum + (portfolio.total_cost_aed ?? 0), 0);

  return {
    portfolio_count: portfolios.length,
    watchlist_count: watchlists.length,
    total_value_aed: totalValue,
    total_return_percent: totalCost ? ((totalValue - totalCost) / totalCost) * 100 : 0,
    watch_items: watchlists.reduce((sum, watchlist) => sum + (watchlist.items?.length ?? 0), 0),
    top_holdings: holdings.slice(0, 4).map((holding) => ({
      symbol: holding.symbol,
      asset_name: holding.asset_name,
      current_value: holding.current_value ?? 0,
      return_percent: holding.unrealized_gain_loss_percent ?? 0,
    })),
  };
}

async function buildWorkspaceFallback(): Promise<MobileWorkspaceSummary> {
  const user = useAuthStore.getState().user;
  if (!user) {
    throw new Error("Authentication required");
  }

  const [featureAccess, portfolios, watchlists, alertIntelligence, notifications, teams, competitors] = await Promise.all([
    mobileApi.getFeatureAccess().catch(() => [] as FeatureAccessItem[]),
    mobileApi.getPortfolios().catch(() => [] as Portfolio[]),
    mobileApi.getWatchlists().catch(() => [] as Watchlist[]),
    mobileApi.getAlertIntelligence().catch(() => null as AlertIntelligence | null),
    mobileApi.getNotifications().catch(() => [] as NotificationItem[]),
    mobileApi.getTeams().catch(() => [] as Team[]),
    mobileApi.getCompetitors().catch(() => [] as Competitor[]),
  ]);

  const enabledFeatures = featureAccess.filter((item) => item.has_access).map((item) => item.feature_key);
  const portfoliosSnapshot = enabledFeatures.includes("portfolios")
    ? buildPortfolioSnapshot(portfolios, watchlists)
    : null;
  const alertsSnapshot = enabledFeatures.includes("alerts") && alertIntelligence
    ? {
        summary: alertIntelligence.summary,
        recent_triggers: alertIntelligence.recent_triggers,
        templates: alertIntelligence.templates,
      }
    : null;
  const competitorSpotlight = enabledFeatures.includes("competitors") && competitors.length
    ? {
        id: competitors[0].id,
        name: competitors[0].name,
        ticker_symbol: competitors[0].ticker_symbol,
        market_share_percent: competitors[0].market_share_percent,
        threat_level: null,
        strategic_note: competitors[0].description,
      }
    : null;

  return {
    user,
    enabled_features: enabledFeatures,
    portfolios: portfoliosSnapshot,
    alerts: alertsSnapshot,
    notifications: {
      unread_count: notifications.filter((item) => !item.is_read).length,
      latest: notifications.slice(0, 8).map((item) => ({
        id: item.id,
        title: item.title,
        message: item.message,
        priority: item.priority,
        created_at: item.created_at,
        is_read: item.is_read,
      })),
    },
    teams_count: teams.length,
    competitor_spotlight: competitorSpotlight,
  };
}

async function buildBootstrapFallback(): Promise<MobileBootstrapResponse> {
  const user = useAuthStore.getState().user;
  const [
    featuredArticles,
    trendingNews,
    marketOverview,
    marketTrend,
    predictionUniverse,
    propertyOptions,
    featureAccess,
  ] = await Promise.all([
    mobileApi.getFeaturedNews().catch(() => [] as NewsArticle[]),
    mobileApi.getNews({ page: 1, page_size: 6 }).catch(
      () =>
        ({
          total: 0,
          page: 1,
          page_size: 6,
          articles: [],
        }) as NewsListResponse,
    ),
    mobileApi.getMarketOverview(),
    mobileApi.getMarketTrend().catch(
      () =>
        ({
          region: "UAE",
          prediction: "neutral",
          confidence: "medium",
          trend_score: 0,
          factors: [],
          recommendation: "Market signal is temporarily unavailable.",
          timeframe: "30-day outlook",
          generated_at: new Date().toISOString(),
        }) as MarketTrendPrediction,
    ),
    mobileApi.getPredictionOptions(),
    mobileApi.getPropertyOptions(),
    apiRequest<FeatureAccessItem[]>(
      {
        method: "GET",
        url: "/settings/feature-access",
      },
      { retryOnUnauthorized: false },
    ).catch(() => [
      {
        feature_key: "news",
        label: "News",
        description: "Mobile news feed",
        category: "core",
        public_access: true,
        grantable: false,
        has_access: true,
      },
      {
        feature_key: "market",
        label: "Market",
        description: "Market intelligence",
        category: "core",
        public_access: true,
        grantable: false,
        has_access: true,
      },
      {
        feature_key: "analytics",
        label: "Analytics",
        description: "Analytics workspace",
        category: "workspace",
        public_access: false,
        grantable: false,
        has_access: false,
      },
      {
        feature_key: "alerts",
        label: "Alerts",
        description: "Alert center",
        category: "workspace",
        public_access: false,
        grantable: false,
        has_access: false,
      },
      {
        feature_key: "settings",
        label: "Settings",
        description: "Profile and controls",
        category: "workspace",
        public_access: false,
        grantable: false,
        has_access: false,
      },
    ]),
  ]);

  const heroArticle = featuredArticles[0] ?? trendingNews.articles[0] ?? null;
  const articles = trendingNews.articles.slice(0, 6);
  const workspaceSummary = user ? await buildWorkspaceFallback().catch(() => null) : null;

  return {
    app_name: appConfig.appName,
    app_version: appConfig.appVersion,
    feature_access: featureAccess,
    hero_article: heroArticle,
    featured_articles: featuredArticles.slice(0, 4),
    trending_articles: articles,
    market_pulse: {
      market_status: marketOverview.market_status,
      movers: marketOverview.stocks.slice(0, 6).map(mapMarketCard),
      real_estate_leaders: marketOverview.real_estate_companies.slice(0, 4).map(mapMarketCard),
      weather: marketOverview.weather
        ? {
            location_name: marketOverview.weather.location_name,
            temperature_c: marketOverview.weather.temperature_c,
            weather_summary: marketOverview.weather.weather_summary,
            observed_at: marketOverview.weather.observed_at,
          }
        : null,
      trend_prediction: marketTrend as unknown as Record<string, unknown>,
    },
    prediction_universe: predictionUniverse,
    property_options: propertyOptions,
    workspace_summary: workspaceSummary,
  };
}

export const mobileApi = {
  getBootstrap: async () => {
    try {
      return await apiRequest<MobileBootstrapResponse>({
        method: "GET",
        url: "/mobile/bootstrap",
      });
    } catch (error) {
      if ((error as { status?: number })?.status === 404) {
        return buildBootstrapFallback();
      }
      throw error;
    }
  },

  getWorkspace: async () => {
    try {
      return await apiRequest<MobileWorkspaceSummary>({
        method: "GET",
        url: "/mobile/workspace",
      });
    } catch (error) {
      if ((error as { status?: number })?.status === 404) {
        return buildWorkspaceFallback();
      }
      throw error;
    }
  },

  getFeatureAccess: () =>
    apiRequest<FeatureAccessItem[]>({
      method: "GET",
      url: "/settings/feature-access",
    }),

  getNews: (filters: NewsFilters = {}) =>
    apiRequest<NewsListResponse>(
      {
        method: "GET",
        url: "/news/",
        params: filters,
      },
      { auth: false },
    ),

  getFeaturedNews: () =>
    apiRequest<NewsArticle[]>(
      {
        method: "GET",
        url: "/news/featured/top",
      },
      { auth: false },
    ),

  getArticle: (articleId: number) =>
    apiRequest<NewsArticle>(
      {
        method: "GET",
        url: `/news/${articleId}`,
      },
      { auth: false },
    ),

  getMarketOverview: () =>
    apiRequest<MarketOverview>(
      {
        method: "GET",
        url: "/market/overview",
      },
      { auth: false },
    ),

  getMarketSymbol: (symbol: string) =>
    apiRequest<MarketData>(
      {
        method: "GET",
        url: `/market/symbol/${symbol}`,
      },
      { auth: false },
    ),

  getPredictionOptions: () =>
    apiRequest<MobileBootstrapResponse["prediction_universe"]>(
      {
        method: "GET",
        url: "/predictions/options",
      },
      { auth: false },
    ),

  getPricePrediction: (symbol: string, daysAhead = 30) =>
    apiRequest<PricePrediction>(
      {
        method: "GET",
        url: `/predictions/price/${encodeURIComponent(symbol)}`,
        params: { days_ahead: daysAhead },
      },
      { auth: false },
    ),

  getMarketTrend: () =>
    apiRequest<MarketTrendPrediction>(
      {
        method: "GET",
        url: "/predictions/market-trend",
      },
      { auth: false },
    ),

  getPropertyOptions: () =>
    apiRequest<MobileBootstrapResponse["property_options"]>(
      {
        method: "GET",
        url: "/market/property-valuation/options",
      },
      { auth: false },
    ),

  getPropertyPreset: (location: string, propertyType: string) =>
    apiRequest<PropertyPreset>(
      {
        method: "GET",
        url: "/market/property-valuation/preset",
        params: { location: location, property_type: propertyType },
      },
      { auth: false },
    ),

  estimateProperty: (payload: {
    area_sqft: number;
    bedrooms: number;
    location: string;
    property_type: string;
    year_built?: number | null;
    amenities?: string[];
  }) =>
    apiRequest<PropertyEstimate>(
      {
        method: "POST",
        url: "/market/property-valuation/estimate",
        data: payload,
      },
      { auth: false },
    ),

  calculateRoi: (payload: {
    purchase_price: number;
    rental_income_monthly: number;
    expenses_monthly: number;
    appreciation_rate: number;
  }) =>
    apiRequest<Record<string, number>>(
      {
        method: "POST",
        url: "/market/property-valuation/roi",
        data: payload,
      },
      { auth: false },
    ),

  getPropertyTrend: (location: string, propertyType: string) =>
    apiRequest<PropertyTrendPrediction>(
      {
        method: "GET",
        url: "/predictions/property-trend",
        params: { location: location, property_type: propertyType },
      },
      { auth: false },
    ),

  getPortfolios: () =>
    apiRequest<Portfolio[]>({
      method: "GET",
      url: "/portfolios/",
    }),

  createPortfolio: (payload: {
    name: string;
    description?: string;
    portfolio_type?: string;
    base_currency?: string;
  }) =>
    apiRequest<Portfolio>({
      method: "POST",
      url: "/portfolios/",
      data: payload,
    }),

  getPortfolio: (portfolioId: number) =>
    apiRequest<Portfolio>({
      method: "GET",
      url: `/portfolios/id/${portfolioId}`,
    }),

  getPortfolioAnalytics: (portfolioId: number) =>
    apiRequest<PortfolioAnalytics>({
      method: "GET",
      url: `/portfolios/id/${portfolioId}/analytics`,
    }),

  addPortfolioTransaction: (
    portfolioId: number,
    payload: {
      transaction_type: string;
      symbol: string;
      quantity: number;
      price: number;
      transaction_date: string;
      fees?: number;
      notes?: string;
    },
  ) =>
    apiRequest({
      method: "POST",
      url: `/portfolios/id/${portfolioId}/transactions`,
      data: payload,
    }),

  getAssetCatalog: () =>
    apiRequest<AssetCatalogItem[]>({
      method: "GET",
      url: "/portfolios/catalog",
    }),

  getWatchlists: () =>
    apiRequest<Watchlist[]>({
      method: "GET",
      url: "/portfolios/watchlists",
    }),

  createWatchlist: (payload: {
    name: string;
    description?: string;
    alert_on_change?: boolean;
    change_threshold_percent?: number;
  }) =>
    apiRequest<Watchlist>({
      method: "POST",
      url: "/portfolios/watchlists",
      data: payload,
    }),

  getAlerts: () =>
    apiRequest<Alert[]>({
      method: "GET",
      url: "/alerts/",
    }),

  createAlert: (payload: Record<string, unknown>) =>
    apiRequest<Alert>({
      method: "POST",
      url: "/alerts/",
      data: payload,
    }),

  toggleAlert: (alertId: number) =>
    apiRequest<{ message: string }>({
      method: "PATCH",
      url: `/alerts/${alertId}/toggle`,
    }),

  getAlertIntelligence: () =>
    apiRequest<AlertIntelligence>({
      method: "GET",
      url: "/alerts/intelligence",
    }),

  getNotifications: () =>
    apiRequest<NotificationItem[]>({
      method: "GET",
      url: "/notifications/",
    }),

  markNotificationRead: (notificationId: number) =>
    apiRequest<{ message: string }>({
      method: "POST",
      url: `/notifications/${notificationId}/read`,
    }),

  getCompetitors: () =>
    apiRequest<Competitor[]>({
      method: "GET",
      url: "/competitors/",
    }),

  getCompetitorCatalog: () =>
    apiRequest<CompetitorCatalogItem[]>(
      {
        method: "GET",
        url: "/competitors/catalog",
      },
      { auth: false },
    ),

  createCompetitor: (payload: Record<string, unknown>) =>
    apiRequest<Competitor>({
      method: "POST",
      url: "/competitors/",
      data: payload,
    }),

  getCompetitorAnalysis: (competitorId: number) =>
    apiRequest<CompetitorAnalysis>({
      method: "GET",
      url: `/competitors/${competitorId}/analysis`,
    }),

  getExecutiveDashboard: () =>
    apiRequest<ExecutiveDashboard>({
      method: "GET",
      url: "/executive/dashboard",
    }),

  getTeams: () =>
    apiRequest<Team[]>({
      method: "GET",
      url: "/teams/",
    }),

  createTeam: (payload: {
    name: string;
    description?: string;
    max_members?: number;
    shared_portfolios?: boolean;
    shared_watchlists?: boolean;
    shared_insights?: boolean;
  }) =>
    apiRequest<Team>({
      method: "POST",
      url: "/teams/",
      data: payload,
    }),

  getTeamActivity: (teamId: number) =>
    apiRequest<Array<Record<string, unknown>>>({
      method: "GET",
      url: `/teams/${teamId}/activity`,
    }),
};

