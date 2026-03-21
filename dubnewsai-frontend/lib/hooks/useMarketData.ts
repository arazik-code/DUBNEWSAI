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
      const { data } = await apiClient.get<MarketOverviewResponse>("/market/overview")
      return data
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
