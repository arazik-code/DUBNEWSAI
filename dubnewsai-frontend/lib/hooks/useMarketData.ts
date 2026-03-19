"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import type { EconomicIndicator, MarketOverviewResponse, MarketStock } from "@/types"

export function useMarketData(limit = 12) {
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
