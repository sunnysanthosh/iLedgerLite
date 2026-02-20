"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useRouter } from "next/navigation"
import { getLedger, createLedgerEntry, settleEntry } from "@/lib/api/ledger"
import { formatCurrency, formatDate, parseDecimal } from "@/lib/utils"
import type { LedgerEntryCreate, LedgerEntryType } from "@/types/api"

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState<Partial<LedgerEntryCreate>>({ type: "debit" })

  const { data, isLoading } = useQuery({
    queryKey: ["ledger", id],
    queryFn: () => getLedger(id),
  })

  const addMutation = useMutation({
    mutationFn: (d: LedgerEntryCreate) => createLedgerEntry(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ledger", id] })
      qc.invalidateQueries({ queryKey: ["customers"] })
      setShowAdd(false)
      setForm({ type: "debit" })
    },
  })

  const settleMutation = useMutation({
    mutationFn: ({ entryId, settled }: { entryId: string; settled: boolean }) =>
      settleEntry(entryId, settled),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ledger", id] }),
  })

  if (isLoading) return <p className="text-sm text-gray-400 p-6">Loading…</p>
  if (!data) return null

  const balance = parseDecimal(data.outstanding_balance)

  return (
    <div className="space-y-5">
      <button onClick={() => router.back()} className="text-sm text-brand-600 hover:underline">
        ← Back to Ledger
      </button>

      {/* Summary */}
      <div className="bg-white rounded-xl border p-5">
        <h2 className="text-xl font-semibold text-gray-900">{data.customer_name}</h2>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <p className="text-xs text-gray-400">Total Debit (given)</p>
            <p className="text-lg font-bold text-green-600">{formatCurrency(data.total_debit)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Total Credit (received)</p>
            <p className="text-lg font-bold text-red-600">{formatCurrency(data.total_credit)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Outstanding</p>
            <p
              className={`text-lg font-bold ${
                balance > 0 ? "text-green-600" : balance < 0 ? "text-red-600" : "text-gray-500"
              }`}
            >
              {formatCurrency(data.outstanding_balance)}
            </p>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => setShowAdd(true)}
          className="bg-brand-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
        >
          + Add Entry
        </button>
      </div>

      {/* Entry timeline */}
      <div className="bg-white rounded-xl border divide-y">
        {data.entries.map((entry) => (
          <div key={entry.id} className="flex items-center justify-between px-5 py-4">
            <div>
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                    entry.type === "debit"
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {entry.type}
                </span>
                {entry.is_settled && (
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                    Settled
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-0.5">{entry.description ?? "—"}</p>
              <p className="text-xs text-gray-400">{formatDate(entry.created_at)}</p>
              {entry.due_date && (
                <p className="text-xs text-orange-500">Due: {formatDate(entry.due_date)}</p>
              )}
            </div>
            <div className="text-right">
              <p
                className={`font-semibold ${
                  entry.type === "debit" ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatCurrency(entry.amount)}
              </p>
              {!entry.is_settled && (
                <button
                  onClick={() => settleMutation.mutate({ entryId: entry.id, settled: true })}
                  className="text-xs text-brand-600 hover:underline mt-1"
                >
                  Mark settled
                </button>
              )}
            </div>
          </div>
        ))}
        {!data.entries.length && (
          <p className="px-5 py-4 text-sm text-gray-400">No entries yet.</p>
        )}
      </div>

      {/* Add entry dialog */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-lg font-semibold">Add Entry</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (!form.amount || !form.type) return
                addMutation.mutate({ ...form, customer_id: id } as LedgerEntryCreate)
              }}
              className="space-y-3"
            >
              <div className="flex gap-2">
                {(["debit", "credit"] as LedgerEntryType[]).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, type: t }))}
                    className={`flex-1 py-1.5 text-sm rounded-lg border capitalize ${
                      form.type === t ? "bg-brand-600 text-white border-brand-600" : "text-gray-600"
                    }`}
                  >
                    {t === "debit" ? "Debit (gave)" : "Credit (received)"}
                  </button>
                ))}
              </div>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                placeholder="Amount"
                value={form.amount ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <input
                type="text"
                placeholder="Description (optional)"
                value={form.description ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value || undefined }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <input
                type="date"
                placeholder="Due date (optional)"
                value={form.due_date ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value || undefined }))}
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
