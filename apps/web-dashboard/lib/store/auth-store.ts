"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { UserProfileWithSettings } from "@/types/api"

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserProfileWithSettings | null
  setAuth: (access: string, refresh: string, user: UserProfileWithSettings) => void
  setUser: (user: UserProfileWithSettings) => void
  setAccessToken: (token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setAuth: (access, refresh, user) =>
        set({ accessToken: access, refreshToken: refresh, user }),

      setUser: (user) => set({ user }),

      setAccessToken: (token) => set({ accessToken: token }),

      logout: () =>
        set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "ledgerlite-auth",
      // Only persist tokens + user — other state is derived
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
)
