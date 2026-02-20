"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { parseDecimal } from "@/lib/utils"
import type { CashflowPeriodData } from "@/types/api"

interface Props {
  data: CashflowPeriodData[]
}

export function CashflowChart({ data }: Props) {
  const chartData = data.map((d) => ({
    period: d.period,
    Inflows:  parseDecimal(d.inflows),
    Outflows: parseDecimal(d.outflows),
    Net:      parseDecimal(d.net),
  }))

  if (!chartData.length) {
    return (
      <div className="h-48 flex items-center justify-center text-sm text-gray-400">
        No cashflow data for selected period.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          formatter={(value: number) =>
            new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(value)
          }
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="Inflows"  stroke="#22c55e" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Outflows" stroke="#ef4444" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Net"      stroke="#3b82f6" strokeWidth={2} dot={false} strokeDasharray="4 2" />
      </LineChart>
    </ResponsiveContainer>
  )
}
