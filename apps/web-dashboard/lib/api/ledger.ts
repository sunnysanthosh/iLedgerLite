import { ledgerClient } from "./client"
import type {
  CustomerCreate,
  CustomerWithBalance,
  LedgerEntryCreate,
  LedgerEntryResponse,
  LedgerSummary,
  PaginatedList,
} from "@/types/api"

// ── Customers ────────────────────────────────────────────────────────────────

export async function getCustomers(
  search?: string,
  skip = 0,
  limit = 20
): Promise<PaginatedList<CustomerWithBalance>> {
  const res = await ledgerClient.get<PaginatedList<CustomerWithBalance>>("/customers", {
    params: { ...(search ? { search } : {}), skip, limit },
  })
  return res.data
}

export async function getCustomer(id: string): Promise<CustomerWithBalance> {
  const res = await ledgerClient.get<CustomerWithBalance>(`/customers/${id}`)
  return res.data
}

export async function createCustomer(data: CustomerCreate): Promise<CustomerWithBalance> {
  const res = await ledgerClient.post<CustomerWithBalance>("/customers", data)
  return res.data
}

// ── Ledger entries ────────────────────────────────────────────────────────────

export async function getLedger(
  customerId: string,
  skip = 0,
  limit = 20
): Promise<LedgerSummary> {
  const res = await ledgerClient.get<LedgerSummary>(`/ledger/${customerId}`, {
    params: { skip, limit },
  })
  return res.data
}

export async function createLedgerEntry(
  data: LedgerEntryCreate
): Promise<LedgerEntryResponse> {
  const res = await ledgerClient.post<LedgerEntryResponse>("/ledger-entry", data)
  return res.data
}

export async function settleEntry(
  id: string,
  is_settled: boolean
): Promise<LedgerEntryResponse> {
  const res = await ledgerClient.put<LedgerEntryResponse>(`/ledger-entry/${id}`, {
    is_settled,
  })
  return res.data
}
