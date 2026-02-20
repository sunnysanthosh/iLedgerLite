"use client"

import { useQuery } from "@tanstack/react-query"
import { getInsights } from "@/lib/api/ai"
import { formatCurrency, parseDecimal } from "@/lib/utils"
import type { TrendDirection } from "@/types/api"

const TREND_STYLE: Record<TrendDirection, { label: string; className: string }> = {
  increasing: { label: "↑ Increasing", className: "text-red-600 bg-red-50" },
  decreasing: { label: "↓ Decreasing", className: "text-green-600 bg-green-50" },
  stable:     { label: "→ Stable",     className: "text-gray-600 bg-gray-100" },
}

export default function AnalyticsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai-insights"],
    queryFn: getInsights,
  })

  if (isLoading) {
    return <p className="text-sm text-gray-400 p-2">Loading AI insights…</p>
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-xl p-5 text-sm">
        AI insights unavailable. Make sure the AI service is running.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Analytics</h2>

      {/* 30-day summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Income (30d)</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {formatCurrency(data?.total_income_30d ?? "0")}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Expenses (30d)</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {formatCurrency(data?.total_expense_30d ?? "0")}
          </p>
        </div>
      </div>

      {/* Spending anomalies */}
      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b">
          <p className="text-sm font-semibold text-gray-700">Spending Anomalies</p>
          <p className="text-xs text-gray-400 mt-0.5">
            Categories where spending deviates significantly from your average
          </p>
        </div>
        {data?.anomalies.length === 0 ? (
          <p className="px-5 py-4 text-sm text-gray-400">No anomalies detected. Great job!</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Category</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Current</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Average</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Deviation</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data?.anomalies.map((a, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-5 py-3 text-gray-800">{a.category_name}</td>
                  <td className="px-5 py-3 text-right font-semibold text-red-600">
                    {formatCurrency(a.current_amount)}
                  </td>
                  <td className="px-5 py-3 text-right text-gray-500">
                    {formatCurrency(a.average_amount)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        a.deviation > 0 ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
                      }`}
                    >
                      {a.deviation > 0 ? "+" : ""}
                      {(a.deviation * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Spending trends */}
      <div className="bg-white rounded-xl border p-5">
        <p className="text-sm font-semibold text-gray-700 mb-4">Spending Trends</p>
        {data?.trends.length === 0 ? (
          <p className="text-sm text-gray-400">Not enough data to calculate trends.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data?.trends.map((t, i) => {
              const style = TREND_STYLE[t.trend]
              return (
                <div key={i} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <p className="font-medium text-gray-800 text-sm">{t.category_name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.className}`}>
                      {style.label}
                    </span>
                  </div>
                  <div className="mt-3 text-xs text-gray-500 space-y-1">
                    <div className="flex justify-between">
                      <span>Last 30d</span>
                      <span className="font-semibold text-gray-800">
                        {formatCurrency(t.last_30_days)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Prior 30d</span>
                      <span className="font-semibold text-gray-800">
                        {formatCurrency(t.previous_30_days)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Top categories */}
      <div className="bg-white rounded-xl border p-5">
        <p className="text-sm font-semibold text-gray-700 mb-4">Top Spending Categories</p>
        <div className="space-y-3">
          {(data?.top_categories ?? []).map((cat, i) => {
            const max = parseDecimal(data?.top_categories[0]?.amount ?? "1")
            const pct = max > 0 ? (parseDecimal(cat.amount) / max) * 100 : 0
            return (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{cat.category_name}</span>
                  <span className="font-semibold text-gray-800">{formatCurrency(cat.amount)}</span>
                </div>
                <div className="h-2 rounded-full bg-gray-100">
                  <div
                    className="h-2 rounded-full bg-brand-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
          {!data?.top_categories?.length && (
            <p className="text-sm text-gray-400">No category data available.</p>
          )}
        </div>
      </div>
    </div>
  )
}
