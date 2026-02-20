"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getAccounts, createAccount, deleteAccount } from "@/lib/api/transactions"
import { formatCurrency, parseDecimal } from "@/lib/utils"
import type { AccountCreate, AccountTypeEnum } from "@/types/api"

const ACCOUNT_ICONS: Record<AccountTypeEnum, string> = {
  cash: "💵",
  bank: "🏦",
  credit_card: "💳",
  wallet: "👜",
  loan: "📋",
}

export default function AccountsPage() {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState<AccountCreate>({ name: "", type: "bank", currency: "INR" })

  const { data: accounts, isLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: getAccounts,
  })

  const addMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      setShowAdd(false)
      setForm({ name: "", type: "bank", currency: "INR" })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["accounts"] }),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Accounts</h2>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-brand-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
        >
          + Add Account
        </button>
      </div>

      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts?.map((acc) => (
          <div key={acc.id} className="bg-white rounded-xl border p-5 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{ACCOUNT_ICONS[acc.type]}</span>
                <div>
                  <p className="font-semibold text-gray-800">{acc.name}</p>
                  <p className="text-xs text-gray-400 capitalize">{acc.type.replace("_", " ")}</p>
                </div>
              </div>
              <button
                onClick={() => deleteMutation.mutate(acc.id)}
                className="text-xs text-red-400 hover:text-red-600"
              >
                Remove
              </button>
            </div>
            <p
              className={`text-xl font-bold ${
                parseDecimal(acc.balance) >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {formatCurrency(acc.balance, acc.currency)}
            </p>
            <p className="text-xs text-gray-400">{acc.currency}</p>
          </div>
        ))}
        {!isLoading && !accounts?.length && (
          <p className="text-sm text-gray-400 col-span-3">
            No accounts yet. Add one to get started.
          </p>
        )}
      </div>

      {/* Add dialog */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-lg font-semibold">Add Account</h3>
            <form
              onSubmit={(e) => { e.preventDefault(); addMutation.mutate(form) }}
              className="space-y-3"
            >
              <input
                type="text"
                required
                placeholder="Account name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <select
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as AccountTypeEnum }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {(["cash", "bank", "credit_card", "wallet", "loan"] as AccountTypeEnum[]).map((t) => (
                  <option key={t} value={t}>{t.replace("_", " ")}</option>
                ))}
              </select>
              <input
                type="text"
                maxLength={3}
                placeholder="Currency (e.g. INR)"
                value={form.currency ?? "INR"}
                onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value.toUpperCase() }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowAdd(false)} className="flex-1 border rounded-lg py-2 text-sm">
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending}
                  className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm disabled:opacity-50"
                >
                  {addMutation.isPending ? "Saving…" : "Add"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
