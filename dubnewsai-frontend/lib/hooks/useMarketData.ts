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

async function buildMarketOverviewFallback(): Promise<MarketOverviewResponse> {
  const [stocksResult, realEstateResult, indicatorsResult, weatherResult] = await Promise.allSettled([
    apiClient.get<MarketStock[]>("/market/stocks", { params: { limit: 24 } }),
    apiClient.get<MarketStock[]>("/market/real-estate-companies"),
    apiClient.get<EconomicIndicator[]>("/market/economic-indicators", { params: { limit: 12 } }),
    apiClient.get<WeatherSnapshot | null>("/market/weather")
  ])

  const boardRows = stocksResult.status === "fulfilled" ? stocksResult.value.data : []
  const realEstateRows = realEstateResult.status === "fulfilled" ? realEstateResult.value.data : []
  const indicators = indicatorsResult.status === "fulfilled" ? indicatorsResult.value.data : []
  const weather = weatherResult.status === "fulfilled" ? weatherResult.value.data : null

  const stocks = boardRows.filter((row) => row.region === "UAE" || row.exchange === "dfm" || row.exchange === "adx")
  const globalRealEstate = realEstateRows.filter((row) => row.region === "International" || (row.exchange !== "dfm" && row.exchange !== "adx"))
  const trackedSymbols = stocks.length + globalRealEstate.length
  const liveSymbols = [...stocks, ...globalRealEstate].filter((row) => row.is_live_data !== false).length
  const fallbackSymbols = Math.max(0, trackedSymbols - liveSymbols)

  return {
    stocks,
    indices: [],
    global_real_estate: globalRealEstate,
    commodities: [],
    currencies: [],
    economic_indicators: indicators,
    real_estate_companies: realEstateRows,
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
      }
    ],
    coverage_snapshot: {
      tracked_symbols: trackedSymbols,
      live_symbols: liveSymbols,
      fallback_symbols: fallbackSymbols,
      fx_pairs: 0,
      macro_indicators: indicators.length,
      provider_count: 0
    },
    provider_utilization: [],
    provider_mix: {
      active_count: 0,
      dormant_count: 0,
      top_contributors: [],
      dormant_providers: []
    },
    intelligence_highlights: [],
    market_brief: {
      headline: "DUBNEWSAI is serving a resilient market fallback view.",
      narrative: "The full overview endpoint is unavailable right now, so the platform is assembling the market surface from the core public board, property coverage, macro indicators, and weather feeds instead of leaving the page blank.",
      focus_areas: [
        `${stocks.length} UAE rows remain visible`,
        `${globalRealEstate.length} global real-estate rows remain visible`,
        `${indicators.length} macro signals are still available`
      ],
      confidence: "medium"
    },
    coverage_alerts: [
      {
        board: "Overview service",
        severity: "medium",
        message: "The full market overview endpoint is currently degraded, so DUBNEWSAI switched to modular fallback queries.",
        action: "Continue using the live board while the overview service refreshes.",
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
