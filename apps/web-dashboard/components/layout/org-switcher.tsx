"use client"

import { useAuthStore } from "@/lib/store/auth-store"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

const ROLE_BADGE: Record<string, string> = {
  owner: "bg-brand-100 text-brand-700",
  member: "bg-gray-100 text-gray-600",
  read_only: "bg-yellow-100 text-yellow-700",
}

export function OrgSwitcher() {
  const organisations = useAuthStore((s) => s.organisations)
  const currentOrgId = useAuthStore((s) => s.currentOrgId)
  const setCurrentOrg = useAuthStore((s) => s.setCurrentOrg)
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)

  // Only show the switcher when the user belongs to more than one org
  if (organisations.length <= 1) return null

  const current = organisations.find((o) => o.id === currentOrgId) ?? organisations[0]

  function handleSelect(orgId: string) {
    setCurrentOrg(orgId)
    setOpen(false)
    // Invalidate all queries so every data view re-fetches with the new X-Org-ID
    queryClient.invalidateQueries()
  }

  return (
    <div className="relative px-3 py-2 border-b">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded-md text-sm bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="truncate font-medium text-gray-800">{current?.name ?? "Select org"}</span>
        <span className="text-gray-400 text-xs shrink-0">▾</span>
      </button>

      {open && (
        <div className="absolute left-3 right-3 top-full mt-1 z-50 bg-white border rounded-lg shadow-lg py-1">
          {organisations.map((org) => (
            <button
              key={org.id}
              onClick={() => handleSelect(org.id)}
              className={`w-full flex items-center justify-between gap-2 px-3 py-2 text-sm hover:bg-gray-50 transition-colors ${
                org.id === currentOrgId ? "bg-brand-50" : ""
              }`}
            >
              <span className="truncate text-gray-800">{org.name}</span>
              <span
                className={`shrink-0 text-xs px-1.5 py-0.5 rounded-full font-medium ${
                  ROLE_BADGE[org.role] ?? "bg-gray-100 text-gray-600"
                }`}
              >
                {org.role.replace("_", " ")}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
