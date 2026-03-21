import axios from "axios"

import { normalizeApiBaseUrl } from "@/lib/config/api"
import { useAuthStore } from "@/lib/store/authStore"

const AUTH_BOOTSTRAP_PATHS = ["/auth/me", "/auth/refresh"]

export class SessionExpiredError extends Error {
  constructor(message = "Your session has expired. Please sign in again.") {
    super(message)
    this.name = "SessionExpiredError"
  }
}

function getApiUrl() {
  if (typeof window !== "undefined") {
    return "/api/backend"
  }

  return normalizeApiBaseUrl()
}

export const apiClient = axios.create({
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 15000
})

const refreshClient = axios.create({
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 15000
})

refreshClient.interceptors.request.use((config) => {
  config.baseURL = getApiUrl()
  return config
})

let refreshPromise: Promise<string | null> | null = null

function decodeJwtPayload(token: string) {
  const [, payload] = token.split(".")
  if (!payload) {
    return null
  }

  const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=")
  const decoded =
    typeof window !== "undefined" ? atob(padded) : Buffer.from(padded, "base64").toString("utf-8")

  return JSON.parse(decoded) as { exp?: number }
}

function isBootstrapAuthRequest(requestUrl: string) {
  return AUTH_BOOTSTRAP_PATHS.some((path) => requestUrl.includes(path))
}

function clearSessionAndRedirect() {
  if (typeof window === "undefined") {
    return
  }

  const { hydrated, accessToken, refreshToken } = useAuthStore.getState()
  if (!hydrated || (!accessToken && !refreshToken)) {
    return
  }

  useAuthStore.getState().clearAuth()
  if (window.location.pathname !== "/login") {
    window.location.href = "/login"
  }
}

function isTokenExpired(token: string) {
  try {
    const decoded = decodeJwtPayload(token)
    if (!decoded?.exp) {
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

  if (!isAuthRequest) {
    const { hydrated, accessToken, refreshToken } = useAuthStore.getState()
    if (hydrated && (accessToken || refreshToken) && !token) {
      throw new SessionExpiredError()
    }
  }

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

    if (error instanceof SessionExpiredError) {
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && isBootstrapAuthRequest(requestUrl)) {
      clearSessionAndRedirect()
    }

    return Promise.reject(error)
  }
)
