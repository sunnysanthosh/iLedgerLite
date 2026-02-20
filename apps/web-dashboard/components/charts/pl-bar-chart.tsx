"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { parseDecimal } from "@/lib/utils"
import type { CategoryAmount } from "@/types/api"

interface Props {
  incomeData:  CategoryAmount[]
  expenseData: CategoryAmount[]
}

export function PLBarChart({ incomeData, expenseData }: Props) {
  // Merge both lists by category name for a grouped bar chart
  const categories = Array.from(
    new Set([...incomeData.map((d) => d.category_name), ...expenseData.map((d) => d.category_name)])
  )

  const chartData = categories.map((cat) => ({
    category: cat.length > 12 ? cat.slice(0, 12) + "…" : cat,
    Income:   parseDecimal(incomeData.find((d) => d.category_name === cat)?.amount ?? "0"),
    Expenses: parseDecimal(expenseData.find((d) => d.category_name === cat)?.amount ?? "0"),
  }))

  if (!chartData.length) {
    return (
      <div className="h-48 flex items-center justify-center text-sm text-gray-400">
        No P&L data for selected period.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="category" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          formatter={(value: number) =>
            new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(value)
          }
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Income"   fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Expenses" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
