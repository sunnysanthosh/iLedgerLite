import { reportClient } from "./client"
import type {
  BudgetResponse,
  CashflowPeriod,
  CashflowResponse,
  ExportResponse,
  ProfitLossResponse,
  SummaryResponse,
} from "@/types/api"

export async function getSummary(): Promise<SummaryResponse> {
  const res = await reportClient.get<SummaryResponse>("/reports/summary")
  return res.data
}

export async function getProfitLoss(
  start_date?: string,
  end_date?: string
): Promise<ProfitLossResponse> {
  const res = await reportClient.get<ProfitLossResponse>("/reports/profit-loss", {
    params: { ...(start_date ? { start_date } : {}), ...(end_date ? { end_date } : {}) },
  })
  return res.data
}

export async function getCashflow(
  start_date?: string,
  end_date?: string,
  period: CashflowPeriod = "monthly"
): Promise<CashflowResponse> {
  const res = await reportClient.get<CashflowResponse>("/reports/cashflow", {
    params: {
      period,
      ...(start_date ? { start_date } : {}),
      ...(end_date ? { end_date } : {}),
    },
  })
  return res.data
}

export async function getBudget(
  start_date?: string,
  end_date?: string
): Promise<BudgetResponse> {
  const res = await reportClient.get<BudgetResponse>("/reports/budget", {
    params: { ...(start_date ? { start_date } : {}), ...(end_date ? { end_date } : {}) },
  })
  return res.data
}

export async function exportCsv(
  start_date?: string,
  end_date?: string
): Promise<ExportResponse> {
  const res = await reportClient.get<ExportResponse>("/reports/export", {
    params: {
      format: "csv",
      ...(start_date ? { start_date } : {}),
      ...(end_date ? { end_date } : {}),
    },
  })
  return res.data
}
