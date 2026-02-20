"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getTransactions,
  getAccounts,
  getCategories,
  createTransaction,
  deleteTransaction,
} from "@/lib/api/transactions"
import { formatCurrency, formatDate } from "@/lib/utils"
import type { TransactionTypeEnum, TransactionCreate } from "@/types/api"

const PAGE_SIZE = 20

export default function TransactionsPage() {
  const qc = useQueryClient()
  const [skip, setSkip] = useState(0)
  const [filterType, setFilterType] = useState<TransactionTypeEnum | "">("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo]     = useState("")
  const [accountId, setAccountId] = useState("")
  const [showAdd, setShowAdd] = useState(false)

  // Form state
  const [form, setForm] = useState<Partial<TransactionCreate>>({
    type: "expense",
    transaction_date: new Date().toISOString().split("T")[0],
  })

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", skip, filterType, dateFrom, dateTo, accountId],
    queryFn: () =>
      getTransactions({
        skip,
        limit: PAGE_SIZE,
        type: filterType || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        account_id: accountId || undefined,
      }),
  })

  const { data: accounts } = useQuery({ queryKey: ["accounts"], queryFn: getAccounts })
  const { data: categories } = useQuery({
    queryKey: ["categories", form.type],
    queryFn: () => getCategories(form.type === "transfer" ? undefined : (form.type as "income" | "expense")),
  })

  const addMutation = useMutation({
    mutationFn: (data: TransactionCreate) => createTransaction(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      qc.invalidateQueries({ queryKey: ["accounts"] })
      setShowAdd(false)
      setForm({ type: "expense", transaction_date: new Date().toISOString().split("T")[0] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] })
      qc.invalidateQueries({ queryKey: ["summary"] })
    },
  })

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE)
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!form.account_id || !form.amount || !form.type || !form.transaction_date) return
    addMutation.mutate(form as TransactionCreate)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Transactions</h2>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-brand-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
        >
          + Add Transaction
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 bg-white border rounded-xl p-4">
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value as TransactionTypeEnum | ""); setSkip(0) }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="transfer">Transfer</option>
        </select>
        <select
          value={accountId}
          onChange={(e) => { setAccountId(e.target.value); setSkip(0) }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All accounts</option>
          {accounts?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); setSkip(0) }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); setSkip(0) }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        />
        {(filterType || accountId || dateFrom || dateTo) && (
          <button
            onClick={() => { setFilterType(""); setAccountId(""); setDateFrom(""); setDateTo(""); setSkip(0) }}
            className="text-sm text-gray-500 hover:text-gray-800 underline"
          >
            Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Date</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Description</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Type</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Amount</th>
              <th className="px-5 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && (
              <tr><td colSpan={5} className="px-5 py-4 text-gray-400 text-center">Loading…</td></tr>
            )}
            {!isLoading && !data?.items.length && (
              <tr><td colSpan={5} className="px-5 py-4 text-gray-400 text-center">No transactions found.</td></tr>
            )}
            {data?.items.map((txn) => (
              <tr key={txn.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-500">{formatDate(txn.transaction_date)}</td>
                <td className="px-5 py-3 text-gray-800">{txn.description ?? "—"}</td>
                <td className="px-5 py-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                      txn.type === "income"
                        ? "bg-green-100 text-green-700"
                        : txn.type === "expense"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {txn.type}
                  </span>
                </td>
                <td
                  className={`px-5 py-3 text-right font-semibold ${
                    txn.type === "income" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {txn.type === "income" ? "+" : "−"}{formatCurrency(txn.amount)}
                </td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => deleteMutation.mutate(txn.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        {(data?.total ?? 0) > PAGE_SIZE && (
          <div className="flex items-center justify-between px-5 py-3 border-t text-sm text-gray-500">
            <span>Page {currentPage} of {totalPages} ({data?.total} total)</span>
            <div className="flex gap-2">
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
                className="px-3 py-1 border rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={skip + PAGE_SIZE >= (data?.total ?? 0)}
                onClick={() => setSkip(skip + PAGE_SIZE)}
                className="px-3 py-1 border rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add dialog */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md space-y-4">
            <h3 className="text-lg font-semibold">Add Transaction</h3>
            <form onSubmit={handleAdd} className="space-y-3">
              <div className="flex gap-2">
                {(["income", "expense", "transfer"] as TransactionTypeEnum[]).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, type: t }))}
                    className={`flex-1 py-1.5 text-sm rounded-lg border capitalize ${
                      form.type === t ? "bg-brand-600 text-white border-brand-600" : "text-gray-600"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <select
                required
                value={form.account_id ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Select account</option>
                {accounts?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <select
                value={form.category_id ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value || undefined }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Category (optional)</option>
                {categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
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
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <input
                type="date"
                required
                value={form.transaction_date ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, transaction_date: e.target.value }))}
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
