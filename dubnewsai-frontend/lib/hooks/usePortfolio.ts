"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import { useAuthStore } from "@/lib/store/authStore"
import type { InvestmentScore, Portfolio, PortfolioAnalytics, PortfolioAssetCatalogItem, Watchlist } from "@/types"

const PORTFOLIO_STANDARD_STALE_TIME = 60 * 1000
const PORTFOLIO_LONG_STALE_TIME = 15 * 60 * 1000

export function usePortfolios() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<Portfolio[]>({
    queryKey: ["portfolios"],
    queryFn: async () => {
      const { data } = await apiClient.get<Portfolio[]>("/portfolios")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: PORTFOLIO_STANDARD_STALE_TIME,
    retry: false
  })
}

export function usePortfolioAnalytics(portfolioId?: number) {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<PortfolioAnalytics>({
    queryKey: ["portfolios", portfolioId, "analytics"],
    queryFn: async () => {
      const { data } = await apiClient.get<PortfolioAnalytics>(`/portfolios/id/${portfolioId}/analytics`)
      return data
    },
    enabled: hydrated && Boolean(accessToken) && Boolean(portfolioId),
    staleTime: PORTFOLIO_STANDARD_STALE_TIME,
    retry: false
  })
}

export function useWatchlists() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<Watchlist[]>({
    queryKey: ["watchlists"],
    queryFn: async () => {
      const { data } = await apiClient.get<Watchlist[]>("/portfolios/watchlists")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: PORTFOLIO_STANDARD_STALE_TIME,
    retry: false
  })
}

export function useInvestmentScore(symbol?: string, riskProfile = "moderate") {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<InvestmentScore>({
    queryKey: ["investment-score", symbol, riskProfile],
    queryFn: async () => {
      const { data } = await apiClient.post<InvestmentScore>(`/portfolios/score/${symbol}`, {
        risk_profile: riskProfile
      })
      return data
    },
    enabled: hydrated && Boolean(accessToken) && Boolean(symbol),
    staleTime: PORTFOLIO_LONG_STALE_TIME,
    retry: false
  })
}

export function usePortfolioAssetCatalog() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<PortfolioAssetCatalogItem[]>({
    queryKey: ["portfolios", "catalog"],
    queryFn: async () => {
      const { data } = await apiClient.get<PortfolioAssetCatalogItem[]>("/portfolios/catalog")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: PORTFOLIO_LONG_STALE_TIME,
    retry: false
  })
}
