import { apiRequest, hydrateStoredSessionState, updatePersistedUser } from "../api/client";
import type { TokenResponse, User } from "../api/types";
import { clearStoredSession, persistSessionTokens } from "../storage/session";
import { useAuthStore } from "../state/auth-store";

async function syncCurrentUser() {
  const user = await apiRequest<User>(
    {
      method: "GET",
      url: "/auth/me",
    },
    {
      auth: true,
      retryOnUnauthorized: true,
    },
  );
  useAuthStore.getState().setUser(user);
  await updatePersistedUser(user);
  return user;
}

export async function hydrateSession() {
  const { markHydrated, clearSession } = useAuthStore.getState();

  try {
    const stored = await hydrateStoredSessionState();
    if (stored) {
      await syncCurrentUser();
    }
  } catch {
    clearSession();
    await clearStoredSession();
  } finally {
    markHydrated();
  }
}

export async function loginWithPassword(email: string, password: string) {
  const { setBusy, setSession } = useAuthStore.getState();
  setBusy(true);
  try {
    const tokens = await apiRequest<TokenResponse>(
      {
        method: "POST",
        url: "/auth/login",
        data: { email, password },
      },
      { auth: false, retryOnUnauthorized: false },
    );

    setSession({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user: null,
    });

    const user = await syncCurrentUser();
    await persistSessionTokens({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user,
    });
    return user;
  } finally {
    useAuthStore.getState().setBusy(false);
  }
}

export async function registerWithPassword(fullName: string, email: string, password: string) {
  const { setBusy } = useAuthStore.getState();
  setBusy(true);
  try {
    await apiRequest<User>(
      {
        method: "POST",
        url: "/auth/register",
        data: {
          full_name: fullName,
          email,
          password,
        },
      },
      { auth: false, retryOnUnauthorized: false },
    );
    return await loginWithPassword(email, password);
  } finally {
    useAuthStore.getState().setBusy(false);
  }
}

export async function logout() {
  useAuthStore.getState().clearSession();
  await clearStoredSession();
}
