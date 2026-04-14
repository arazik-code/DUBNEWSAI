"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import type {
  ComparativeAnalysisResponse,
  EconomicIndicator,
  MarketIntelligenceResponse,
  MarketOverviewResponse,
  MarketStock,
  PropertyValuationOptionsResponse,
  PropertyValuationPresetResponse,
  PropertyValuationResponse,
  ROIResponse,
  WeatherSnapshot
} from "@/types"

const MARKET_FAST_STALE_TIME = 60 * 1000
const MARKET_STANDARD_STALE_TIME = 5 * 60 * 1000
const MARKET_LONG_STALE_TIME = 30 * 60 * 1000

function countLiveRows(rows: MarketStock[]) {
  return rows.filter((row) => row.is_live_data !== false).length
}

function buildProviderMix(
  providerUtilization: NonNullable<MarketOverviewResponse["provider_utilization"]>
): NonNullable<MarketOverviewResponse["provider_mix"]> {
  const active = providerUtilization.filter((item) => item.total_calls > 0)
  const dormant = providerUtilization.filter((item) => item.total_calls === 0).map((item) => item.provider)
  const ranked = [...providerUtilization].sort((left, right) => {
    const leftScore = left.successful_calls + left.total_calls
    const rightScore = right.successful_calls + right.total_calls
    return rightScore - leftScore
  })

  return {
    active_count: active.length,
    dormant_count: dormant.length,
    top_contributors: ranked.slice(0, 5).map((item) => item.provider),
    dormant_providers: dormant.slice(0, 6)
  }
}

async function buildMarketOverviewFallback(): Promise<MarketOverviewResponse> {
  const [stocksResult, globalResult, indicesResult, commoditiesResult, currenciesResult, providerResult, indicatorsResult, weatherResult] =
    await Promise.allSettled([
    apiClient.get<MarketStock[]>("/market/stocks", { params: { limit: 40 } }),
    apiClient.get<MarketStock[]>("/market/global-real-estate", { params: { limit: 16 } }),
    apiClient.get<MarketStock[]>("/market/indices", { params: { limit: 10 } }),
    apiClient.get<MarketStock[]>("/market/commodities", { params: { limit: 10 } }),
    apiClient.get<MarketOverviewResponse["currencies"]>("/market/currencies", { params: { limit: 10 } }),
    apiClient.get<NonNullable<MarketOverviewResponse["provider_utilization"]>>("/market/provider-utilization", { params: { limit: 8 } }),
    apiClient.get<EconomicIndicator[]>("/market/economic-indicators", { params: { limit: 12 } }),
    apiClient.get<WeatherSnapshot | null>("/market/weather")
  ])

  const boardRows = stocksResult.status === "fulfilled" ? stocksResult.value.data : []
  const stocks = boardRows.filter((row) => row.region === "UAE" || row.exchange === "dfm" || row.exchange === "adx")
  const globalRealEstate = globalResult.status === "fulfilled"
    ? globalResult.value.data
    : boardRows.filter((row) => row.region === "International" || (row.exchange !== "dfm" && row.exchange !== "adx" && row.market_type === "stock"))
  const indices = indicesResult.status === "fulfilled"
    ? indicesResult.value.data
    : boardRows.filter((row) => row.market_type === "index")
  const commodities = commoditiesResult.status === "fulfilled"
    ? commoditiesResult.value.data
    : boardRows.filter((row) => row.market_type === "commodity")
  const currencies = currenciesResult.status === "fulfilled" ? currenciesResult.value.data : []
  const providerUtilization = providerResult.status === "fulfilled" ? providerResult.value.data : []
  const indicators = indicatorsResult.status === "fulfilled" ? indicatorsResult.value.data : []
  const weather = weatherResult.status === "fulfilled" ? weatherResult.value.data : null

  const trackedSymbols = stocks.length + globalRealEstate.length + indices.length + commodities.length
  const liveSymbols = countLiveRows(stocks) + countLiveRows(globalRealEstate) + countLiveRows(indices) + countLiveRows(commodities)
  const fallbackSymbols = Math.max(0, trackedSymbols - liveSymbols)
  const providerMix = buildProviderMix(providerUtilization)

  return {
    stocks,
    indices,
    global_real_estate: globalRealEstate,
    commodities,
    currencies,
    economic_indicators: indicators,
    real_estate_companies: [...stocks, ...globalRealEstate].filter((row) => row.market_type === "stock"),
    weather,
    market_status: null,
    board_health: [
      {
        board: "UAE market board",
        status: stocks.length ? (stocks.some((row) => row.is_live_data === false) ? "mixed" : "live") : "empty",
        total_rows: stocks.length,
        live_rows: stocks.filter((row) => row.is_live_data !== false).length,
        fallback_rows: stocks.filter((row) => row.is_live_data === false).length,
        last_updated: stocks[0]?.data_timestamp ?? null,
        providers: Array.from(new Set(stocks.map((row) => row.primary_provider).filter(Boolean) as string[]))
      },
      {
        board: "Global real-estate board",
        status: globalRealEstate.length ? (globalRealEstate.some((row) => row.is_live_data === false) ? "mixed" : "live") : "empty",
        total_rows: globalRealEstate.length,
        live_rows: globalRealEstate.filter((row) => row.is_live_data !== false).length,
        fallback_rows: globalRealEstate.filter((row) => row.is_live_data === false).length,
        last_updated: globalRealEstate[0]?.data_timestamp ?? null,
        providers: Array.from(new Set(globalRealEstate.map((row) => row.primary_provider).filter(Boolean) as string[]))
      },
      {
        board: "Indices",
        status: indices.length ? (indices.some((row) => row.is_live_data === false) ? "mixed" : "live") : "empty",
        total_rows: indices.length,
        live_rows: countLiveRows(indices),
        fallback_rows: indices.filter((row) => row.is_live_data === false).length,
        last_updated: indices[0]?.data_timestamp ?? null,
        providers: Array.from(new Set(indices.map((row) => row.primary_provider).filter(Boolean) as string[]))
      },
      {
        board: "Commodities",
        status: commodities.length ? (commodities.some((row) => row.is_live_data === false) ? "mixed" : "live") : "empty",
        total_rows: commodities.length,
        live_rows: countLiveRows(commodities),
        fallback_rows: commodities.filter((row) => row.is_live_data === false).length,
        last_updated: commodities[0]?.data_timestamp ?? null,
        providers: Array.from(new Set(commodities.map((row) => row.primary_provider).filter(Boolean) as string[]))
      }
    ],
    coverage_snapshot: {
      tracked_symbols: trackedSymbols,
      live_symbols: liveSymbols,
      fallback_symbols: fallbackSymbols,
      fx_pairs: currencies.length,
      macro_indicators: indicators.length,
      provider_count: providerUtilization.length
    },
    provider_utilization: providerUtilization,
    provider_mix: providerMix,
    intelligence_highlights: [],
    market_brief: {
      headline: "DUBNEWSAI is serving a resilient market fallback view.",
      narrative: "The full overview endpoint is unavailable right now, so the platform is rebuilding the market surface from the live UAE board, global real-estate board, indices, commodities, FX, macro indicators, and weather feeds instead of leaving the page blank.",
      focus_areas: [
        `${stocks.length} UAE rows remain visible`,
        `${globalRealEstate.length} global real-estate rows remain visible`,
        `${currencies.length} FX pairs remain visible`,
        `${indicators.length} macro signals are still available`
      ],
      confidence: "medium"
    },
    coverage_alerts: [
      {
        board: "Overview service",
        severity: "medium",
        message: "The full market overview endpoint is currently degraded, so DUBNEWSAI switched to modular fallback queries.",
        action: "Continue using the live board while the overview service refreshes and the platform preserves the full multi-board context.",
        affected_symbols: []
      }
    ]
  }
}

export function useMarketData(limit = 24) {
  return useQuery<MarketStock[]>({
    queryKey: ["market", "stocks", limit],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketStock[]>("/market/stocks", { params: { limit } })
      return data
    },
    staleTime: MARKET_FAST_STALE_TIME
  })
}

export function useMarketSymbol(symbol: string) {
  return useQuery<MarketStock>({
    queryKey: ["market", "symbol", symbol],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketStock>(`/market/symbol/${symbol}`)
      return data
    },
    enabled: Boolean(symbol),
    staleTime: MARKET_FAST_STALE_TIME
  })
}

export function useMarketOverview() {
  return useQuery<MarketOverviewResponse>({
    queryKey: ["market", "overview"],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get<MarketOverviewResponse>("/market/overview")
        return data
      } catch {
        return buildMarketOverviewFallback()
      }
    },
    staleTime: MARKET_FAST_STALE_TIME
  })
}

export function useEconomicIndicators(limit = 12) {
  return useQuery<EconomicIndicator[]>({
    queryKey: ["market", "economic-indicators", limit],
    queryFn: async () => {
      const { data } = await apiClient.get<EconomicIndicator[]>("/market/economic-indicators", {
        params: { limit }
      })
      return data
    },
    staleTime: MARKET_STANDARD_STALE_TIME
  })
}

export function useMarketWeather() {
  return useQuery<WeatherSnapshot | null>({
    queryKey: ["market", "weather"],
    queryFn: async () => {
      const { data } = await apiClient.get<WeatherSnapshot | null>("/market/weather")
      return data
    },
    staleTime: MARKET_STANDARD_STALE_TIME
  })
}

export function useMarketIntelligence(region = "UAE") {
  return useQuery<MarketIntelligenceResponse>({
    queryKey: ["analytics", "market-intelligence", region],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketIntelligenceResponse>("/analytics/market-intelligence", {
        params: { region }
      })
      return data
    },
    staleTime: MARKET_STANDARD_STALE_TIME
  })
}

export type PropertyValuationApi = PropertyValuationResponse
export type PropertyRoiApi = ROIResponse
export type PropertyCmaApi = ComparativeAnalysisResponse

export function usePropertyValuationOptions() {
  return useQuery<PropertyValuationOptionsResponse>({
    queryKey: ["market", "property-valuation", "options"],
    queryFn: async () => {
      const { data } = await apiClient.get<PropertyValuationOptionsResponse>("/market/property-valuation/options")
      return data
    },
    staleTime: MARKET_LONG_STALE_TIME
  })
}

export function usePropertyValuationPreset(location?: string, propertyType = "Apartment") {
  return useQuery<PropertyValuationPresetResponse>({
    queryKey: ["market", "property-valuation", "preset", location, propertyType],
    queryFn: async () => {
      const { data } = await apiClient.get<PropertyValuationPresetResponse>("/market/property-valuation/preset", {
        params: {
          location,
          property_type: propertyType
        }
      })
      return data
    },
    enabled: Boolean(location),
    staleTime: MARKET_STANDARD_STALE_TIME
  })
}
