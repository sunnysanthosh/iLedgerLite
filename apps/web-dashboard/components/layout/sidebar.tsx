"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const NAV = [
  { href: "/dashboard",    label: "Dashboard",     icon: "▦" },
  { href: "/transactions", label: "Transactions",  icon: "↕" },
  { href: "/accounts",     label: "Accounts",      icon: "🏦" },
  { href: "/ledger",       label: "Ledger",        icon: "📒" },
  { href: "/reports",      label: "Reports",       icon: "📊" },
  { href: "/analytics",    label: "Analytics",     icon: "🤖" },
  { href: "/settings",     label: "Settings",      icon: "⚙" },
  { href: "/infra",        label: "Infra Costs",   icon: "☁" },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 bg-white border-r flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b">
        <p className="text-lg font-bold text-brand-700">LedgerLite</p>
        <p className="text-xs text-gray-400 mt-0.5">Web Dashboard</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-3">
        {NAV.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-brand-50 text-brand-700 font-medium"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t">
        <p className="text-xs text-gray-400">© 2025 LedgerLite</p>
      </div>
    </aside>
  )
}
