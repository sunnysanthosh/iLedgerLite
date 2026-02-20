"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { getProfitLoss, getCashflow, getBudget, exportCsv } from "@/lib/api/reports"
import { formatCurrency, parseDecimal, startOfCurrentMonth, today } from "@/lib/utils"
import { PLBarChart } from "@/components/charts/pl-bar-chart"
import { CashflowChart } from "@/components/charts/cashflow-chart"
import type { CashflowPeriod } from "@/types/api"

export default function ReportsPage() {
  const [startDate, setStartDate] = useState(startOfCurrentMonth())
  const [endDate, setEndDate]     = useState(today())
  const [cfPeriod, setCfPeriod]   = useState<CashflowPeriod>("monthly")

  const { data: pl } = useQuery({
    queryKey: ["profit-loss", startDate, endDate],
    queryFn: () => getProfitLoss(startDate, endDate),
  })

  const { data: cashflow } = useQuery({
    queryKey: ["cashflow", startDate, endDate, cfPeriod],
    queryFn: () => getCashflow(startDate, endDate, cfPeriod),
  })

  const { data: budget } = useQuery({
    queryKey: ["budget", startDate, endDate],
    queryFn: () => getBudget(startDate, endDate),
  })

  async function handleExport() {
    const result = await exportCsv(startDate, endDate)
    const blob = new Blob([result.data], { type: result.content_type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = result.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-xl font-semibold text-gray-900 mr-2">Reports</h2>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm"
        />
        <span className="text-gray-400 text-sm">to</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm"
        />
        <button
          onClick={handleExport}
          className="ml-auto border border-brand-600 text-brand-600 text-sm px-4 py-1.5 rounded-lg hover:bg-brand-50 transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* P&L summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Income</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {formatCurrency(pl?.total_income ?? "0")}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Expenses</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {formatCurrency(pl?.total_expenses ?? "0")}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Net Profit</p>
          <p
            className={`text-2xl font-bold mt-1 ${
              parseDecimal(pl?.net_profit ?? "0") >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {formatCurrency(pl?.net_profit ?? "0")}
          </p>
        </div>
      </div>

      {/* P&L chart */}
      <div className="bg-white rounded-xl border p-5">
        <p className="text-sm font-semibold text-gray-700 mb-4">Income vs Expenses by Category</p>
        <PLBarChart
          incomeData={pl?.income_by_category ?? []}
          expenseData={pl?.expense_by_category ?? []}
        />
      </div>

      {/* Cashflow chart */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-gray-700">Cashflow</p>
          <div className="flex gap-1">
            {(["daily", "weekly", "monthly"] as CashflowPeriod[]).map((p) => (
              <button
                key={p}
                onClick={() => setCfPeriod(p)}
                className={`px-3 py-1 text-xs rounded-lg capitalize ${
                  cfPeriod === p ? "bg-brand-600 text-white" : "border text-gray-600"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <CashflowChart data={cashflow?.periods ?? []} />
      </div>

      {/* Budget breakdown */}
      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b flex justify-between">
          <p className="text-sm font-semibold text-gray-700">Spending by Category</p>
          <p className="text-sm text-gray-500">
            Total: {formatCurrency(budget?.total_spent ?? "0")}
          </p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Category</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Spent</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Transactions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(budget?.categories ?? []).map((cat, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-800">{cat.category_name}</td>
                <td className="px-5 py-3 text-right font-semibold text-red-600">
                  {formatCurrency(cat.spent)}
                </td>
                <td className="px-5 py-3 text-right text-gray-500">{cat.transaction_count}</td>
              </tr>
            ))}
            {!budget?.categories?.length && (
              <tr><td colSpan={3} className="px-5 py-4 text-center text-gray-400">No data for selected period.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
