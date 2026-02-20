"use client"

import { usePathname, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/lib/store/auth-store"
import { getNotifications } from "@/lib/api/notifications"

const PAGE_TITLES: Record<string, string> = {
  "/dashboard":    "Dashboard",
  "/transactions": "Transactions",
  "/accounts":     "Accounts",
  "/ledger":       "Ledger",
  "/reports":      "Reports",
  "/analytics":    "Analytics",
  "/settings":     "Settings",
}

export function Header() {
  const pathname = usePathname()
  const router   = useRouter()
  const { user, logout } = useAuthStore()

  const { data: notifs } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => getNotifications(0, 1, true),
    refetchInterval: 60_000,  // Poll every minute
  })

  const unreadCount = notifs?.unread_count ?? 0

  const title =
    Object.entries(PAGE_TITLES).find(([path]) => pathname === path || pathname.startsWith(path + "/"))?.[1] ??
    "LedgerLite"

  function handleLogout() {
    logout()
    router.push("/login")
  }

  return (
    <header className="h-14 bg-white border-b flex items-center justify-between px-6 shrink-0">
      <h1 className="text-base font-semibold text-gray-800">{title}</h1>

      <div className="flex items-center gap-4">
        {/* Notification bell */}
        <button
          onClick={() => router.push("/settings")}
          className="relative text-gray-500 hover:text-gray-800"
          title="Notifications"
        >
          <span className="text-xl">🔔</span>
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center leading-none">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {/* User menu */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-medium select-none">
            {user?.full_name?.charAt(0).toUpperCase() ?? "?"}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-gray-700 leading-tight">{user?.full_name}</p>
            <p className="text-xs text-gray-400 leading-tight">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-1 text-xs text-gray-400 hover:text-gray-700 border rounded px-2 py-1"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
