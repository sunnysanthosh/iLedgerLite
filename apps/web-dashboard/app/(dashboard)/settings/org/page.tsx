"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/lib/store/auth-store"
import { getOrg, inviteMember, removeMember, updateMemberRole } from "@/lib/api/orgs"
import type { OrgMemberResponse } from "@/types/api"

const ROLE_OPTIONS = [
  { value: "owner",     label: "Owner" },
  { value: "member",    label: "Member" },
  { value: "read_only", label: "Read Only" },
]

export default function OrgSettingsPage() {
  const currentOrgId = useAuthStore((s) => s.currentOrgId)
  const queryClient = useQueryClient()
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<"member" | "read_only">("member")
  const [inviteError, setInviteError] = useState<string | null>(null)

  const { data: org, isLoading } = useQuery({
    queryKey: ["org", currentOrgId],
    queryFn: () => getOrg(currentOrgId!),
    enabled: !!currentOrgId,
  })

  const inviteMutation = useMutation({
    mutationFn: () => inviteMember(currentOrgId!, { email: inviteEmail, role: inviteRole }),
    onSuccess: () => {
      setInviteEmail("")
      setInviteError(null)
      queryClient.invalidateQueries({ queryKey: ["org", currentOrgId] })
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setInviteError(msg ?? "Failed to invite member")
    },
  })

  const removeMutation = useMutation({
    mutationFn: (userId: string) => removeMember(currentOrgId!, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["org", currentOrgId] }),
  })

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateMemberRole(currentOrgId!, userId, { role: role as "owner" | "member" | "read_only" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["org", currentOrgId] }),
  })

  if (!currentOrgId) {
    return <p className="text-gray-500">No organisation selected.</p>
  }

  if (isLoading) {
    return <div className="text-gray-400 py-8 text-center">Loading…</div>
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{org?.name ?? "Organisation"}</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {org?.is_personal ? "Personal organisation" : "Shared organisation"}
        </p>
      </div>

      {/* Members list */}
      <section className="bg-white rounded-xl border p-5 space-y-4">
        <h2 className="font-semibold text-gray-800">Members</h2>
        <div className="divide-y">
          {(org?.members ?? []).map((m: OrgMemberResponse) => (
            <div key={m.user_id} className="flex items-center justify-between py-3 gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{m.full_name}</p>
                <p className="text-xs text-gray-400 truncate">{m.email}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <select
                  value={m.role}
                  onChange={(e) => roleMutation.mutate({ userId: m.user_id, role: e.target.value })}
                  className="text-xs border rounded px-2 py-1 text-gray-700 bg-white"
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
                <button
                  onClick={() => removeMutation.mutate(m.user_id)}
                  className="text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50 transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Invite form */}
      {!org?.is_personal && (
        <section className="bg-white rounded-xl border p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Invite member</h2>
          <div className="flex gap-3">
            <input
              type="email"
              placeholder="email@example.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as "member" | "read_only")}
              className="border rounded-lg px-3 py-2 text-sm text-gray-700"
            >
              <option value="member">Member</option>
              <option value="read_only">Read Only</option>
            </select>
            <button
              onClick={() => inviteMutation.mutate()}
              disabled={!inviteEmail || inviteMutation.isPending}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              Invite
            </button>
          </div>
          {inviteError && <p className="text-sm text-red-600">{inviteError}</p>}
        </section>
      )}
    </div>
  )
}
