"use client"

import { useQuery } from "@tanstack/react-query"
import { getSummary } from "@/lib/api/reports"
import { getAccounts } from "@/lib/api/transactions"
import { getTransactions } from "@/lib/api/transactions"
import { formatCurrency, formatDate, parseDecimal } from "@/lib/utils"
import { CashflowChart } from "@/components/charts/cashflow-chart"
import { getCashflow } from "@/lib/api/reports"
import { startOfCurrentMonth, today } from "@/lib/utils"

function StatCard({
  label,
  value,
  sub,
  positive,
}: {
  label: string
  value: string
  sub?: string
  positive?: boolean
}) {
  return (
    <div className="bg-white rounded-xl border p-5">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
      <p
        className={`text-2xl font-bold mt-1 ${
          positive === undefined
            ? "text-gray-900"
            : positive
            ? "text-green-600"
            : "text-red-600"
        }`}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["summary"],
    queryFn: getSummary,
  })

  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: getAccounts,
  })

  const { data: recentTxns } = useQuery({
    queryKey: ["transactions", "recent"],
    queryFn: () => getTransactions({ limit: 10 }),
  })

  const { data: cashflow } = useQuery({
    queryKey: ["cashflow", "daily"],
    queryFn: () => getCashflow(startOfCurrentMonth(), today(), "daily"),
  })

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Overview</h2>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Balance" value={formatCurrency(summary?.total_balance ?? "0")} />
        <StatCard
          label="Income"
          value={formatCurrency(summary?.total_income ?? "0")}
          positive={true}
        />
        <StatCard
          label="Expenses"
          value={formatCurrency(summary?.total_expenses ?? "0")}
          positive={false}
        />
        <StatCard
          label="Net Profit"
          value={formatCurrency(summary?.net_profit ?? "0")}
          positive={parseDecimal(summary?.net_profit ?? "0") >= 0}
          sub={`${summary?.transaction_count ?? 0} transactions`}
        />
      </div>

      {/* Cashflow chart + accounts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border p-5">
          <p className="text-sm font-semibold text-gray-700 mb-4">Cashflow — This Month</p>
          <CashflowChart data={cashflow?.periods ?? []} />
        </div>

        <div className="bg-white rounded-xl border p-5">
          <p className="text-sm font-semibold text-gray-700 mb-3">Accounts</p>
          <div className="space-y-3">
            {(accounts ?? []).map((acc) => (
              <div key={acc.id} className="flex justify-between items-center text-sm">
                <div>
                  <p className="font-medium text-gray-800">{acc.name}</p>
                  <p className="text-xs text-gray-400 capitalize">{acc.type.replace("_", " ")}</p>
                </div>
                <p
                  className={`font-semibold ${
                    parseDecimal(acc.balance) >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {formatCurrency(acc.balance)}
                </p>
              </div>
            ))}
            {!accounts?.length && (
              <p className="text-sm text-gray-400">No accounts yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent transactions */}
      <div className="bg-white rounded-xl border">
        <div className="px-5 py-4 border-b">
          <p className="text-sm font-semibold text-gray-700">Recent Transactions</p>
        </div>
        <div className="divide-y">
          {(recentTxns?.items ?? []).map((txn) => (
            <div key={txn.id} className="flex items-center justify-between px-5 py-3 text-sm">
              <div>
                <p className="font-medium text-gray-800">
                  {txn.description ?? "—"}
                </p>
                <p className="text-xs text-gray-400">{formatDate(txn.transaction_date)}</p>
              </div>
              <div className="text-right">
                <p
                  className={`font-semibold ${
                    txn.type === "income" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {txn.type === "income" ? "+" : "−"}
                  {formatCurrency(txn.amount)}
                </p>
                <p className="text-xs text-gray-400 capitalize">{txn.type}</p>
              </div>
            </div>
          ))}
          {!recentTxns?.items?.length && (
            <p className="px-5 py-4 text-sm text-gray-400">No transactions yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
