import { aiClient } from "./client"
import type { CategorizeResponse, InsightsResponse, TransactionTypeEnum } from "@/types/api"

export async function getInsights(): Promise<InsightsResponse> {
  const res = await aiClient.get<InsightsResponse>("/ai/insights")
  return res.data
}

export async function categorize(
  description: string,
  amount: string,
  type: "income" | "expense" = "expense"
): Promise<CategorizeResponse> {
  const res = await aiClient.post<CategorizeResponse>("/ai/categorize", {
    description,
    amount,
    type,
  })
  return res.data
}
