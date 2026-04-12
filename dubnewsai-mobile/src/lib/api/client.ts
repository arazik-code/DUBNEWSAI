import axios, { type AxiosRequestConfig } from "axios";

import { appConfig } from "../config";
import { clearStoredSession, loadStoredSession, persistSessionTokens, saveStoredSession } from "../storage/session";
import { useAuthStore } from "../state/auth-store";
import type { TokenResponse, UserSession } from "./types";

const http = axios.create({
  baseURL: appConfig.apiUrl,
  timeout: 20000,
});

let refreshPromise: Promise<string | null> | null = null;

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(message: string, status = 500, detail = message) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function parseApiError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 500;
    const detail =
      (typeof error.response?.data?.detail === "string" && error.response.data.detail) ||
      error.message ||
      "Unexpected API error";
    return new ApiError(detail, status, detail);
  }

  return new ApiError("Unexpected network error");
}

async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const { refreshToken, user, clearSession, setSession } = useAuthStore.getState();
    if (!refreshToken) {
      return null;
    }

    try {
      const response = await http.post<TokenResponse>("/auth/refresh", undefined, {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      });

      const nextSession: UserSession = {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        user,
      };
      setSession(nextSession);
      await persistSessionTokens(nextSession);
      return response.data.access_token;
    } catch {
      clearSession();
      await clearStoredSession();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiRequest<T>(
  config: AxiosRequestConfig,
  options: { auth?: boolean; retryOnUnauthorized?: boolean } = {},
): Promise<T> {
  const { auth = true, retryOnUnauthorized = true } = options;
  const { accessToken } = useAuthStore.getState();
  const headers: Record<string, string> = {
    ...(config.headers as Record<string, string> | undefined),
  };

  if (auth && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  try {
    const response = await http.request<T>({
      ...config,
      headers,
    });
    return response.data;
  } catch (error) {
    if (
      auth &&
      retryOnUnauthorized &&
      axios.isAxiosError(error) &&
      error.response?.status === 401 &&
      useAuthStore.getState().refreshToken
    ) {
      const nextAccessToken = await refreshAccessToken();
      if (nextAccessToken) {
        return apiRequest<T>(
          {
            ...config,
            headers: {
              ...(config.headers as Record<string, string> | undefined),
              Authorization: `Bearer ${nextAccessToken}`,
            },
          },
          {
            auth: false,
            retryOnUnauthorized: false,
          },
        );
      }
    }

    throw parseApiError(error);
  }
}

export async function hydrateStoredSessionState() {
  const stored = await loadStoredSession();
  if (!stored) {
    return null;
  }
  useAuthStore.getState().setSession({
    accessToken: stored.accessToken,
    refreshToken: stored.refreshToken,
    user: stored.user,
  });
  return stored;
}

export async function updatePersistedUser(user: UserSession["user"]) {
  const stored = await loadStoredSession();
  if (!stored) {
    return;
  }
  await saveStoredSession({
    accessToken: stored.accessToken,
    refreshToken: stored.refreshToken,
    user,
  });
}
