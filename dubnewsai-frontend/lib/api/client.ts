import axios from "axios"

import { normalizeApiBaseUrl } from "@/lib/config/api"
import { useAuthStore } from "@/lib/store/authStore"

function getApiUrl() {
  return normalizeApiBaseUrl()
}

export const apiClient = axios.create({
  baseURL: getApiUrl(),
  headers: {
    "Content-Type": "application/json"
  }
})

const refreshClient = axios.create({
  baseURL: getApiUrl(),
  headers: {
    "Content-Type": "application/json"
  }
})

let refreshPromise: Promise<string | null> | null = null

function isTokenExpired(token: string) {
  try {
    const [, payload] = token.split(".")
    if (!payload) {
      return true
    }
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
    const decoded = JSON.parse(atob(normalized)) as { exp?: number }
    if (!decoded.exp) {
      return true
    }
    return decoded.exp * 1000 <= Date.now() + 30_000
  } catch {
    return true
  }
}

async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise
  }

  const refreshToken = useAuthStore.getState().refreshToken
  if (!refreshToken) {
    return null
  }

  refreshPromise = refreshClient
    .post("/auth/refresh", null, {
      baseURL: getApiUrl(),
      headers: {
        Authorization: `Bearer ${refreshToken}`
      }
    })
    .then((response) => {
      const nextTokens = response.data as { access_token: string; refresh_token: string }
      useAuthStore.getState().setTokens(nextTokens.access_token, nextTokens.refresh_token)
      return nextTokens.access_token
    })
    .catch(() => {
      useAuthStore.getState().clearAuth()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export async function ensureValidAccessToken() {
  const { accessToken, refreshToken } = useAuthStore.getState()

  if (accessToken && !isTokenExpired(accessToken)) {
    return accessToken
  }

  if (!refreshToken) {
    return accessToken
  }

  return refreshAccessToken()
}

apiClient.interceptors.request.use(async (config) => {
  config.baseURL = getApiUrl()
  const requestUrl = String(config.url || "")
  const isAuthRequest =
    requestUrl.includes("/auth/login") ||
    requestUrl.includes("/auth/register") ||
    requestUrl.includes("/auth/refresh")

  const token = isAuthRequest ? useAuthStore.getState().accessToken : await ensureValidAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as (typeof error.config & { _retry?: boolean }) | undefined
    const requestUrl = String(originalRequest?.url || "")

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const isAuthRequest =
        requestUrl.includes("/auth/login") ||
        requestUrl.includes("/auth/register") ||
        requestUrl.includes("/auth/refresh")

      if (!isAuthRequest) {
        originalRequest._retry = true
        const nextAccessToken = await refreshAccessToken()
        if (nextAccessToken) {
          originalRequest.headers = originalRequest.headers ?? {}
          originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`
          return apiClient(originalRequest)
        }
      }
    }

    if (typeof window !== "undefined" && error.response?.status === 401) {
      const { hydrated, accessToken } = useAuthStore.getState()
      if (hydrated && accessToken) {
        useAuthStore.getState().clearAuth()
      }
      if (hydrated && accessToken && window.location.pathname !== "/login") {
        window.location.href = "/login"
      }
    }

    return Promise.reject(error)
  }
)
