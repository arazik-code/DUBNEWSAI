import { create } from "zustand";

import type { User } from "../api/types";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isHydrated: boolean;
  isBusy: boolean;
  setBusy: (value: boolean) => void;
  markHydrated: () => void;
  setSession: (payload: { accessToken: string; refreshToken: string; user?: User | null }) => void;
  setUser: (user: User | null) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrated: false,
  isBusy: false,
  setBusy: (value) => set({ isBusy: value }),
  markHydrated: () => set({ isHydrated: true }),
  setSession: ({ accessToken, refreshToken, user }) =>
    set((state) => ({
      accessToken,
      refreshToken,
      user: user ?? state.user,
    })),
  setUser: (user) => set({ user }),
  clearSession: () =>
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isBusy: false,
    }),
}));
