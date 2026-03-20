"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import type { InvestmentScore, Portfolio, PortfolioAnalytics, Watchlist } from "@/types"

export function usePortfolios() {
  return useQuery<Portfolio[]>({
    queryKey: ["portfolios"],
    queryFn: async () => {
      const { data } = await apiClient.get<Portfolio[]>("/portfolios")
      return data
    }
  })
}

export function usePortfolioAnalytics(portfolioId?: number) {
  return useQuery<PortfolioAnalytics>({
    queryKey: ["portfolios", portfolioId, "analytics"],
    queryFn: async () => {
      const { data } = await apiClient.get<PortfolioAnalytics>(`/portfolios/id/${portfolioId}/analytics`)
      return data
    },
    enabled: Boolean(portfolioId)
  })
}

export function useWatchlists() {
  return useQuery<Watchlist[]>({
    queryKey: ["watchlists"],
    queryFn: async () => {
      const { data } = await apiClient.get<Watchlist[]>("/portfolios/watchlists")
      return data
    }
  })
}

export function useInvestmentScore(symbol?: string, riskProfile = "moderate") {
  return useQuery<InvestmentScore>({
    queryKey: ["investment-score", symbol, riskProfile],
    queryFn: async () => {
      const { data } = await apiClient.post<InvestmentScore>(`/portfolios/score/${symbol}`, {
        risk_profile: riskProfile
      })
      return data
    },
    enabled: Boolean(symbol)
  })
}
