"use client"

import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api/client"
import { useAuthStore } from "@/lib/store/authStore"
import type {
  ApiKeyRecord,
  CompetitorCatalogItem,
  Competitor,
  CompetitorAnalysis,
  ExecutiveDashboard,
  FeatureAccess,
  FeatureAccessUser,
  MarketTrendPrediction,
  PredictionUniverseResponse,
  PricePrediction,
  PropertyTrendPrediction,
  TeamDirectoryUser,
  Team,
  TeamActivity,
  WhiteLabelConfig
} from "@/types"

const SHORT_LIVED_STALE_TIME = 60 * 1000
const STANDARD_STALE_TIME = 5 * 60 * 1000
const LONG_LIVED_STALE_TIME = 30 * 60 * 1000

export function useCompetitors() {
  return useQuery<Competitor[]>({
    queryKey: ["competitors"],
    queryFn: async () => {
      const { data } = await apiClient.get<Competitor[]>("/competitors")
      return data
    },
    staleTime: STANDARD_STALE_TIME
  })
}

export function useFeatureAccess() {
  return useQuery<FeatureAccess[]>({
    queryKey: ["feature-access"],
    queryFn: async () => {
      const { data } = await apiClient.get<FeatureAccess[]>("/settings/feature-access")
      return data
    },
    staleTime: STANDARD_STALE_TIME,
    refetchOnMount: false,
    retry: false
  })
}

export function useAdminFeatureAccessUsers() {
  const { accessToken, hydrated, user } = useAuthStore()

  return useQuery<FeatureAccessUser[]>({
    queryKey: ["admin", "feature-access", "users"],
    queryFn: async () => {
      const { data } = await apiClient.get<FeatureAccessUser[]>("/admin/feature-access/users")
      return data
    },
    enabled: hydrated && Boolean(accessToken) && user?.role === "admin",
    staleTime: STANDARD_STALE_TIME,
    refetchOnMount: false,
    retry: false
  })
}

export function useAdminFeatureAccess(userId?: number) {
  const { accessToken, hydrated, user } = useAuthStore()

  return useQuery<FeatureAccess[]>({
    queryKey: ["admin", "feature-access", userId],
    queryFn: async () => {
      const { data } = await apiClient.get<FeatureAccess[]>(`/admin/feature-access/users/${userId}`)
      return data
    },
    enabled: hydrated && Boolean(accessToken) && user?.role === "admin" && Boolean(userId),
    staleTime: STANDARD_STALE_TIME,
    retry: false
  })
}

export function useCompetitorCatalog() {
  return useQuery<CompetitorCatalogItem[]>({
    queryKey: ["competitors", "catalog"],
    queryFn: async () => {
      const { data } = await apiClient.get<CompetitorCatalogItem[]>("/competitors/catalog")
      return data
    },
    staleTime: LONG_LIVED_STALE_TIME
  })
}

export function useCompetitorAnalysis(competitorId?: number) {
  return useQuery<CompetitorAnalysis>({
    queryKey: ["competitors", competitorId, "analysis"],
    queryFn: async () => {
      const { data } = await apiClient.get<CompetitorAnalysis>(`/competitors/${competitorId}/analysis`)
      return data
    },
    enabled: Boolean(competitorId),
    staleTime: STANDARD_STALE_TIME
  })
}

export function usePricePrediction(symbol?: string, daysAhead = 30) {
  return useQuery<PricePrediction>({
    queryKey: ["predictions", "price", symbol, daysAhead],
    queryFn: async () => {
      const { data } = await apiClient.get<PricePrediction>(`/predictions/price/${symbol}`, { params: { days_ahead: daysAhead } })
      return data
    },
    enabled: Boolean(symbol),
    staleTime: LONG_LIVED_STALE_TIME
  })
}

export function usePredictionUniverse() {
  return useQuery<PredictionUniverseResponse>({
    queryKey: ["predictions", "options"],
    queryFn: async () => {
      const { data } = await apiClient.get<PredictionUniverseResponse>("/predictions/options")
      return data
    },
    staleTime: LONG_LIVED_STALE_TIME
  })
}

export function useMarketTrend(region = "UAE") {
  return useQuery<MarketTrendPrediction>({
    queryKey: ["predictions", "market-trend", region],
    queryFn: async () => {
      const { data } = await apiClient.get<MarketTrendPrediction>("/predictions/market-trend", { params: { region } })
      return data
    },
    staleTime: STANDARD_STALE_TIME
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
    enabled: Boolean(location),
    staleTime: STANDARD_STALE_TIME
  })
}

export function useExecutiveDashboard(period = "30d") {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<ExecutiveDashboard>({
    queryKey: ["executive", period],
    queryFn: async () => {
      const { data } = await apiClient.get<ExecutiveDashboard>("/executive/dashboard", { params: { time_period: period } })
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: SHORT_LIVED_STALE_TIME,
    retry: false
  })
}

export function useTeams() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<Team[]>({
    queryKey: ["teams"],
    queryFn: async () => {
      const { data } = await apiClient.get<Team[]>("/teams")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: SHORT_LIVED_STALE_TIME,
    retry: false
  })
}

export function useTeamActivity(teamId?: number) {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<TeamActivity[]>({
    queryKey: ["teams", teamId, "activity"],
    queryFn: async () => {
      const { data } = await apiClient.get<TeamActivity[]>(`/teams/${teamId}/activity`)
      return data
    },
    enabled: hydrated && Boolean(accessToken) && Boolean(teamId),
    staleTime: SHORT_LIVED_STALE_TIME,
    retry: false
  })
}

export function useTeamDirectory(query = "") {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<TeamDirectoryUser[]>({
    queryKey: ["teams", "directory", query],
    queryFn: async () => {
      const { data } = await apiClient.get<TeamDirectoryUser[]>("/teams/directory", { params: { query } })
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: LONG_LIVED_STALE_TIME,
    retry: false
  })
}

export function useApiKeys() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<ApiKeyRecord[]>({
    queryKey: ["settings", "api-keys"],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiKeyRecord[]>("/settings/api-keys")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: SHORT_LIVED_STALE_TIME,
    retry: false
  })
}

export function useWhiteLabelConfig() {
  const { accessToken, hydrated } = useAuthStore()

  return useQuery<WhiteLabelConfig | null>({
    queryKey: ["settings", "white-label"],
    queryFn: async () => {
      const { data } = await apiClient.get<WhiteLabelConfig | null>("/settings/white-label")
      return data
    },
    enabled: hydrated && Boolean(accessToken),
    staleTime: SHORT_LIVED_STALE_TIME,
    retry: false
  })
}
