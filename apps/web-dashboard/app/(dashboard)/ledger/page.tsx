"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { getCustomers, createCustomer } from "@/lib/api/ledger"
import { formatCurrency, parseDecimal } from "@/lib/utils"
import type { CustomerCreate } from "@/types/api"

export default function LedgerPage() {
  const router = useRouter()
  const qc = useQueryClient()
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState<CustomerCreate>({ name: "" })

  const { data, isLoading } = useQuery({
    queryKey: ["customers", debouncedSearch],
    queryFn: () => getCustomers(debouncedSearch || undefined),
  })

  const addMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customers"] })
      setShowAdd(false)
      setForm({ name: "" })
    },
  })

  function handleSearchChange(v: string) {
    setSearch(v)
    clearTimeout((window as unknown as { _st?: ReturnType<typeof setTimeout> })._st)
    ;(window as unknown as { _st?: ReturnType<typeof setTimeout> })._st = setTimeout(
      () => setDebouncedSearch(v),
      300
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Ledger</h2>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-brand-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
        >
          + Add Customer
        </button>
      </div>

      <input
        type="text"
        placeholder="Search customers by name or phone…"
        value={search}
        onChange={(e) => handleSearchChange(e.target.value)}
        className="w-full border rounded-xl px-4 py-2 text-sm"
      />

      <div className="bg-white rounded-xl border divide-y">
        {isLoading && <p className="px-5 py-4 text-sm text-gray-400">Loading…</p>}
        {!isLoading && !data?.items.length && (
          <p className="px-5 py-4 text-sm text-gray-400">
            {search ? "No customers match your search." : "No customers yet."}
          </p>
        )}
        {data?.items.map((c) => {
          const bal = parseDecimal(c.outstanding_balance)
          return (
            <button
              key={c.id}
              onClick={() => router.push(`/ledger/${c.id}`)}
              className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 text-left"
            >
              <div>
                <p className="font-medium text-gray-800">{c.name}</p>
                {c.phone && <p className="text-xs text-gray-400">{c.phone}</p>}
              </div>
              <div className="text-right">
                <p
                  className={`font-semibold text-sm ${
                    bal > 0 ? "text-green-600" : bal < 0 ? "text-red-600" : "text-gray-400"
                  }`}
                >
                  {formatCurrency(c.outstanding_balance)}
                </p>
                <p className="text-xs text-gray-400">
                  {bal > 0 ? "owes you" : bal < 0 ? "you owe" : "settled"}
                </p>
              </div>
            </button>
          )
        })}
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-lg font-semibold">Add Customer</h3>
            <form
              onSubmit={(e) => { e.preventDefault(); addMutation.mutate(form) }}
              className="space-y-3"
            >
              <input
                required
                placeholder="Name *"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <input
                placeholder="Phone (optional)"
                value={form.phone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value || undefined }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <input
                placeholder="Email (optional)"
                value={form.email ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value || undefined }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowAdd(false)} className="flex-1 border rounded-lg py-2 text-sm">Cancel</button>
                <button type="submit" disabled={addMutation.isPending} className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm disabled:opacity-50">
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
