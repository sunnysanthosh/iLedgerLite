"use client"

import { useQuery } from "@tanstack/react-query"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts"
import type { ResourceCost, SprintSnapshot, BudgetLine, CostTrend } from "@/app/api/infra/costs/route"

interface CostsPayload {
  resources: ResourceCost[]
  budgets: BudgetLine[]
  snapshots: SprintSnapshot[]
  trends: CostTrend[]
  totals: { staging: number; production: number }
  note: string
}

async function fetchCosts(): Promise<CostsPayload> {
  const res = await fetch("/api/infra/costs")
  if (!res.ok) throw new Error("Failed to load cost data")
  return res.json()
}

function usd(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n)
}

function BudgetBar({ label, current, cap, alertAt }: { label: string; current: number; cap: number; alertAt: number }) {
  const pct = cap > 0 ? Math.min((current / cap) * 100, 100) : 0
  const color = current >= alertAt ? "bg-red-500" : current >= alertAt * 0.6 ? "bg-amber-400" : "bg-green-500"
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-500">{usd(current)} / {usd(cap)} cap &nbsp;·&nbsp; alert at {usd(alertAt)}</span>
      </div>
      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function InfraPage() {
  const { data, isLoading, error } = useQuery<CostsPayload>({
    queryKey: ["infra-costs"],
    queryFn: fetchCosts,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <div className="text-sm text-gray-400 p-4">Loading cost data…</div>
  if (error || !data) return <div className="text-sm text-red-500 p-4">Failed to load cost data.</div>

  const trendData = data.trends.map((t) => ({
    month: t.month,
    Staging: t.staging,
    Production: t.production ?? 0,
  }))

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Infra Costs</h2>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Staging (monthly est.)</p>
          <p className="text-2xl font-bold text-brand-700 mt-1">{usd(data.totals.staging)}</p>
          <p className="text-xs text-gray-400 mt-0.5">Nightly-off model · cap {usd(150)}</p>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Production (projected)</p>
          <p className="text-2xl font-bold text-gray-400 mt-1">{usd(data.totals.production)}</p>
          <p className="text-xs text-gray-400 mt-0.5">Not yet deployed · cap {usd(650)}</p>
        </div>
      </div>

      {/* Budget progress bars */}
      <div className="bg-white rounded-xl border p-5 space-y-4">
        <p className="text-sm font-semibold text-gray-700">Budget vs Actual</p>
        {data.budgets.map((b) => (
          <BudgetBar key={b.environment} label={b.environment} current={b.currentEstimate} cap={b.cap} alertAt={b.alertAt} />
        ))}
      </div>

      {/* 3-month trend chart */}
      <div className="bg-white rounded-xl border p-5">
        <p className="text-sm font-semibold text-gray-700 mb-4">3-Month Spend Trend (USD/month)</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={trendData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
            <Tooltip formatter={(v: number) => `$${v}/mo`} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="Staging" stroke="#2B6BAE" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Production" stroke="#E68A2E" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="4 2" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Resource breakdown table */}
      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b">
          <p className="text-sm font-semibold text-gray-700">Resource Breakdown</p>
          <p className="text-xs text-gray-400 mt-0.5">{data.note}</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Resource</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Spec</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Staging/mo</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Prod/mo</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.resources.map((r) => (
              <tr key={r.name} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-800 font-medium">{r.name}</td>
                <td className="px-5 py-3 text-gray-500 text-xs">{r.spec}</td>
                <td className="px-5 py-3 text-right font-semibold text-brand-700">
                  {r.stagingMonthly > 0 ? usd(r.stagingMonthly) : "—"}
                </td>
                <td className="px-5 py-3 text-right text-gray-400">
                  {r.productionMonthly != null && r.productionMonthly > 0 ? usd(r.productionMonthly) : "—"}
                </td>
              </tr>
            ))}
            <tr className="bg-gray-50 font-semibold">
              <td className="px-5 py-3 text-gray-800" colSpan={2}>Total</td>
              <td className="px-5 py-3 text-right text-brand-700">{usd(data.totals.staging)}</td>
              <td className="px-5 py-3 text-right text-gray-500">{usd(data.totals.production)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Sprint-exit snapshots */}
      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b">
          <p className="text-sm font-semibold text-gray-700">Sprint-Exit Cost Snapshots</p>
          <p className="text-xs text-gray-400 mt-0.5">Appended automatically by cost-snapshot.yml on every sprint tag</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Sprint</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Date</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Staging</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Production</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.snapshots.map((s: SprintSnapshot) => (
              <tr key={s.sprint} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-800">{s.sprint}</td>
                <td className="px-5 py-3 text-gray-500">{s.date}</td>
                <td className="px-5 py-3 text-right text-brand-700 font-medium">{s.stagingCost}</td>
                <td className="px-5 py-3 text-right text-gray-400">{s.productionCost}</td>
                <td className="px-5 py-3 text-gray-500 text-xs">{s.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
