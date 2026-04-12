import * as SecureStore from "expo-secure-store";

import type { User, UserSession } from "../api/types";

const SESSION_KEY = "dubnewsai.mobile.session";

export type PersistedSession = {
  accessToken: string;
  refreshToken: string;
  user: User | null;
};

export async function loadStoredSession(): Promise<PersistedSession | null> {
  const raw = await SecureStore.getItemAsync(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as PersistedSession;
    if (!parsed.accessToken || !parsed.refreshToken) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export async function saveStoredSession(session: PersistedSession) {
  await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(session));
}

export async function persistSessionTokens(session: UserSession) {
  await saveStoredSession({
    accessToken: session.accessToken,
    refreshToken: session.refreshToken,
    user: session.user,
  });
}

export async function clearStoredSession() {
  await SecureStore.deleteItemAsync(SESSION_KEY);
}
