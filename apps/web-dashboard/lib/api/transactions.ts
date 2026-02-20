import { transactionClient } from "./client"
import type {
  AccountCreate,
  AccountResponse,
  CategoryCreate,
  CategoryResponse,
  PaginatedList,
  TransactionCreate,
  TransactionFilters,
  TransactionResponse,
  TransactionUpdate,
} from "@/types/api"

// ── Accounts ─────────────────────────────────────────────────────────────────

export async function getAccounts(): Promise<AccountResponse[]> {
  const res = await transactionClient.get<AccountResponse[]>("/accounts")
  return res.data
}

export async function createAccount(data: AccountCreate): Promise<AccountResponse> {
  const res = await transactionClient.post<AccountResponse>("/accounts", data)
  return res.data
}

export async function deleteAccount(id: string): Promise<void> {
  await transactionClient.delete(`/accounts/${id}`)
}

// ── Categories ────────────────────────────────────────────────────────────────

export async function getCategories(type?: "income" | "expense"): Promise<CategoryResponse[]> {
  const res = await transactionClient.get<CategoryResponse[]>("/categories", {
    params: type ? { type } : undefined,
  })
  return res.data
}

export async function createCategory(data: CategoryCreate): Promise<CategoryResponse> {
  const res = await transactionClient.post<CategoryResponse>("/categories", data)
  return res.data
}

// ── Transactions ──────────────────────────────────────────────────────────────

export async function getTransactions(
  filters: TransactionFilters = {}
): Promise<PaginatedList<TransactionResponse>> {
  const params: Record<string, unknown> = {}
  if (filters.account_id)  params.account_id  = filters.account_id
  if (filters.category_id) params.category_id = filters.category_id
  if (filters.type)        params.type        = filters.type
  if (filters.date_from)   params.date_from   = filters.date_from
  if (filters.date_to)     params.date_to     = filters.date_to
  params.skip  = filters.skip  ?? 0
  params.limit = filters.limit ?? 20

  const res = await transactionClient.get<PaginatedList<TransactionResponse>>(
    "/transactions",
    { params }
  )
  return res.data
}

export async function createTransaction(data: TransactionCreate): Promise<TransactionResponse> {
  const res = await transactionClient.post<TransactionResponse>("/transactions", data)
  return res.data
}

export async function updateTransaction(
  id: string,
  data: TransactionUpdate
): Promise<TransactionResponse> {
  const res = await transactionClient.put<TransactionResponse>(`/transactions/${id}`, data)
  return res.data
}

export async function deleteTransaction(id: string): Promise<void> {
  await transactionClient.delete(`/transactions/${id}`)
}
