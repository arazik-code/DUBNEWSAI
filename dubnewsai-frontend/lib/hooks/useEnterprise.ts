"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import type {
  ApiKeyRecord,
  Competitor,
  CompetitorAnalysis,
  ExecutiveDashboard,
  MarketTrendPrediction,
  PricePrediction,
  PropertyTrendPrediction,
  Team,
  TeamActivity,
  WhiteLabelConfig
} from "@/types"

export function useCompetitors() {
  return useQuery<Competitor[]>({
    queryKey: ["competitors"],
    queryFn: async () => {
      const { data } = await apiClient.get<Competitor[]>("/competitors")
      return data
    }
  })
}

export function useCompetitorAnalysis(competitorId?: number) {
  return useQuery<CompetitorAnalysis>({
    queryKey: ["competitors", competitorId, "analysis"],
    queryFn: async () => {
      const { data } = await apiClient.get<CompetitorAnalysis>(`/competitors/${competitorId}/analysis`)
      return data
    },
    enabled: Boolean(competitorId)
  })
}

export function usePricePrediction(symbol?: string, daysAhead = 30) {
  return useQuery<PricePrediction>({
    queryKey: ["predictions", "price", symbol, daysAhead],
    queryFn: async () => {
      const { data } = await apiClient.get<PricePrediction>(`/predictions/price/${symbol}`, { params: { days_ahead: daysAhead } })
      return data
    },
    enabled: Boolean(symbol)
  })
}

export function useMarketTrend(region = "UAE") {
  return useQuery<MarketTrendPrediction>({
    queryKey: ["predictions", "market-trend", region],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketTrendPrediction>("/predictions/market-trend", { params: { region } })
      return data
    }
  })
}

export function usePropertyTrend(location?: string, propertyType = "apartment") {
  return useQuery<PropertyTrendPrediction>({
    queryKey: ["predictions", "property-trend", location, propertyType],
    queryFn: async () => {
      const { data } = await apiClient.get<PropertyTrendPrediction>("/predictions/property-trend", {
        params: { location, property_type: propertyType }
      })
      return data
    },
    enabled: Boolean(location)
  })
}

export function useExecutiveDashboard(period = "30d") {
  return useQuery<ExecutiveDashboard>({
    queryKey: ["executive", period],
    queryFn: async () => {
      const { data } = await apiClient.get<ExecutiveDashboard>("/executive/dashboard", { params: { time_period: period } })
      return data
    }
  })
}

export function useTeams() {
  return useQuery<Team[]>({
    queryKey: ["teams"],
    queryFn: async () => {
      const { data } = await apiClient.get<Team[]>("/teams")
      return data
    }
  })
}

export function useTeamActivity(teamId?: number) {
  return useQuery<TeamActivity[]>({
    queryKey: ["teams", teamId, "activity"],
    queryFn: async () => {
      const { data } = await apiClient.get<TeamActivity[]>(`/teams/${teamId}/activity`)
      return data
    },
    enabled: Boolean(teamId)
  })
}

export function useApiKeys() {
  return useQuery<ApiKeyRecord[]>({
    queryKey: ["settings", "api-keys"],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiKeyRecord[]>("/settings/api-keys")
      return data
    }
  })
}

export function useWhiteLabelConfig() {
  return useQuery<WhiteLabelConfig | null>({
    queryKey: ["settings", "white-label"],
    queryFn: async () => {
      const { data } = await apiClient.get<WhiteLabelConfig | null>("/settings/white-label")
      return data
    }
  })
}
