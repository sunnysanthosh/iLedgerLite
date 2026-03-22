"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth-store"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"
import { authClient } from "@/lib/api/client"
import type { UserProfile } from "@/types/api"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const accessToken = useAuthStore((s) => s.accessToken)
  const organisations = useAuthStore((s) => s.organisations)
  const setOrganisations = useAuthStore((s) => s.setOrganisations)

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login")
      return
    }
    // Hydrate org list from /auth/me when store is empty (e.g. first load after token restore)
    if (organisations.length === 0) {
      authClient.get<UserProfile>("/auth/me").then((res) => {
        const orgs = res.data.organisations ?? []
        if (orgs.length > 0) setOrganisations(orgs)
      }).catch(() => {
        // silently ignore — user stays on personal org fallback
      })
    }
  }, [accessToken, organisations.length, router, setOrganisations])

  if (!accessToken) return null

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
