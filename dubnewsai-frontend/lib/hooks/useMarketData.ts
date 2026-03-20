"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import type {
  ComparativeAnalysisResponse,
  EconomicIndicator,
  MarketIntelligenceResponse,
  MarketOverviewResponse,
  MarketStock,
  PropertyValuationResponse,
  ROIResponse,
  WeatherSnapshot
} from "@/types"

export function useMarketData(limit = 24) {
  return useQuery<MarketStock[]>({
    queryKey: ["market", "stocks", limit],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketStock[]>("/market/stocks", { params: { limit } })
      return data
    }
  })
}

export function useMarketSymbol(symbol: string) {
  return useQuery<MarketStock>({
    queryKey: ["market", "symbol", symbol],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketStock>(`/market/symbol/${symbol}`)
      return data
    },
    enabled: Boolean(symbol)
  })
}

export function useMarketOverview() {
  return useQuery<MarketOverviewResponse>({
    queryKey: ["market", "overview"],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketOverviewResponse>("/market/overview")
      return data
    }
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
    }
  })
}

export function useMarketWeather() {
  return useQuery<WeatherSnapshot | null>({
    queryKey: ["market", "weather"],
    queryFn: async () => {
      const { data } = await apiClient.get<WeatherSnapshot | null>("/market/weather")
      return data
    }
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
    }
  })
}

export type PropertyValuationApi = PropertyValuationResponse
export type PropertyRoiApi = ROIResponse
export type PropertyCmaApi = ComparativeAnalysisResponse
