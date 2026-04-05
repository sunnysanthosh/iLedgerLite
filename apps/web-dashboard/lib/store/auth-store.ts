"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { OrgRef, UserProfileWithSettings } from "@/types/api"

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserProfileWithSettings | null
  currentOrgId: string | null
  organisations: OrgRef[]
  setAuth: (access: string, refresh: string, user: UserProfileWithSettings) => void
  setUser: (user: UserProfileWithSettings) => void
  setAccessToken: (token: string) => void
  setCurrentOrg: (orgId: string) => void
  setOrganisations: (orgs: OrgRef[]) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      currentOrgId: null,
      organisations: [],

      setAuth: (access, refresh, user) => {
        const orgs = user.organisations ?? []
        const personalOrg = orgs.find((o) => o.is_personal) ?? orgs[0] ?? null
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
          organisations: orgs,
          currentOrgId: personalOrg?.id ?? null,
        })
      },

      setUser: (user) => {
        const orgs = user.organisations ?? []
        set((state) => ({
          user,
          organisations: orgs.length > 0 ? orgs : state.organisations,
          currentOrgId:
            state.currentOrgId ??
            (orgs.find((o) => o.is_personal) ?? orgs[0])?.id ??
            null,
        }))
      },

      setAccessToken: (token) => set({ accessToken: token }),

      setCurrentOrg: (orgId) => set({ currentOrgId: orgId }),

      setOrganisations: (orgs) =>
        set((state) => ({
          organisations: orgs,
          currentOrgId:
            state.currentOrgId ??
            (orgs.find((o) => o.is_personal) ?? orgs[0])?.id ??
            null,
        })),

      logout: () =>
        set({ accessToken: null, refreshToken: null, user: null, currentOrgId: null, organisations: [] }),
    }),
    {
      name: "ledgerlite-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        currentOrgId: state.currentOrgId,
        organisations: state.organisations,
      }),
    }
  )
)
