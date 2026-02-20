// TypeScript interfaces matching all LedgerLite Pydantic response schemas.
// Decimal amounts are returned as strings from the API for precision.

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: string
  email: string
  full_name: string
  phone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  phone?: string
}

export interface LoginRequest {
  email: string
  password: string
}

// ─── User / Settings ─────────────────────────────────────────────────────────

export type AccountType = "personal" | "business" | "both"
export type Language = "en" | "hi" | "ta" | "te"

export interface UserSettings {
  account_type: AccountType
  currency: string
  language: Language
  business_category: string | null
  notifications_enabled: boolean
  onboarding_completed: boolean
}

export interface UserProfileWithSettings extends UserProfile {
  settings: UserSettings
}

export interface UserUpdate {
  full_name?: string
  phone?: string
  email?: string
}

export interface SettingsUpdate {
  notifications_enabled?: boolean
  language?: Language
  currency?: string
}

export interface OnboardingRequest {
  account_type: AccountType
  currency: string
  language: Language
  business_category?: string
}

// ─── Accounts ────────────────────────────────────────────────────────────────

export type AccountTypeEnum = "cash" | "bank" | "credit_card" | "wallet" | "loan"

export interface AccountResponse {
  id: string
  user_id: string
  name: string
  type: AccountTypeEnum
  currency: string
  balance: string   // Decimal as string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AccountCreate {
  name: string
  type: AccountTypeEnum
  currency?: string
}

// ─── Categories ──────────────────────────────────────────────────────────────

export type TransactionTypeEnum = "income" | "expense" | "transfer"

export interface CategoryResponse {
  id: string
  user_id: string | null
  name: string
  type: "income" | "expense"
  icon: string | null
  is_system: boolean
  created_at: string
}

export interface CategoryCreate {
  name: string
  type: "income" | "expense"
  icon?: string
}

// ─── Transactions ─────────────────────────────────────────────────────────────

export interface TransactionResponse {
  id: string
  user_id: string
  account_id: string
  category_id: string | null
  type: TransactionTypeEnum
  amount: string  // Decimal as string
  description: string | null
  transaction_date: string
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  account_id: string
  category_id?: string
  type: TransactionTypeEnum
  amount: string
  description?: string
  transaction_date: string
}

export interface TransactionUpdate {
  amount?: string
  description?: string
  type?: TransactionTypeEnum
}

export interface PaginatedList<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface TransactionFilters {
  account_id?: string
  category_id?: string
  type?: TransactionTypeEnum
  date_from?: string
  date_to?: string
  skip?: number
  limit?: number
}

// ─── Ledger ──────────────────────────────────────────────────────────────────

export interface CustomerResponse {
  id: string
  user_id: string
  name: string
  phone: string | null
  email: string | null
  address: string | null
  created_at: string
  updated_at: string
}

export interface CustomerWithBalance extends CustomerResponse {
  outstanding_balance: string  // Decimal as string; positive = owed to you
}

export interface CustomerCreate {
  name: string
  phone?: string
  email?: string
  address?: string
}

export type LedgerEntryType = "debit" | "credit"

export interface LedgerEntryResponse {
  id: string
  user_id: string
  customer_id: string
  type: LedgerEntryType
  amount: string  // Decimal as string
  description: string | null
  due_date: string | null
  is_settled: boolean
  created_at: string
  updated_at: string
}

export interface LedgerEntryCreate {
  customer_id: string
  amount: string
  type: LedgerEntryType
  due_date?: string
  description?: string
}

export interface LedgerSummary {
  customer_id: string
  customer_name: string
  total_debit: string
  total_credit: string
  outstanding_balance: string
  entries: LedgerEntryResponse[]
  total: number
  skip: number
  limit: number
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export interface CategoryAmount {
  category_id: string | null
  category_name: string
  amount: string
}

export interface SummaryResponse {
  total_balance: string
  total_income: string
  total_expenses: string
  net_profit: string
  transaction_count: number
  account_count: number
  top_expense_categories: CategoryAmount[]
  top_income_categories: CategoryAmount[]
  outstanding_receivables: string
  outstanding_payables: string
}

export interface ProfitLossResponse {
  start_date: string
  end_date: string
  total_income: string
  total_expenses: string
  net_profit: string
  income_by_category: CategoryAmount[]
  expense_by_category: CategoryAmount[]
}

export type CashflowPeriod = "daily" | "weekly" | "monthly"

export interface CashflowPeriodData {
  period: string
  inflows: string
  outflows: string
  net: string
}

export interface CashflowResponse {
  start_date: string
  end_date: string
  period: CashflowPeriod
  periods: CashflowPeriodData[]
  total_inflows: string
  total_outflows: string
  net_cashflow: string
}

export interface BudgetCategory {
  category_id: string | null
  category_name: string
  spent: string
  transaction_count: number
}

export interface BudgetResponse {
  start_date: string
  end_date: string
  categories: BudgetCategory[]
  total_spent: string
}

export interface ExportResponse {
  format: string
  filename: string
  content_type: string
  data: string  // CSV text
}

// ─── Notifications ────────────────────────────────────────────────────────────

export type NotificationType = "reminder" | "payment" | "overdue" | "system"

export interface NotificationResponse {
  id: string
  user_id: string
  type: NotificationType
  title: string
  message: string
  is_read: boolean
  related_entity_id: string | null
  created_at: string
}

export interface NotificationList {
  items: NotificationResponse[]
  total: number
  skip: number
  limit: number
  unread_count: number
}

// ─── AI / Analytics ──────────────────────────────────────────────────────────

export interface CategoryPrediction {
  category_id: string | null
  category_name: string
  confidence: number
}

export interface CategorizeResponse {
  predictions: CategoryPrediction[]
}

export interface SpendingAnomaly {
  category_name: string
  current_amount: string
  average_amount: string
  deviation: number
}

export type TrendDirection = "increasing" | "decreasing" | "stable"

export interface SpendingTrend {
  category_name: string
  trend: TrendDirection
  last_30_days: string
  previous_30_days: string
}

export interface InsightsResponse {
  anomalies: SpendingAnomaly[]
  trends: SpendingTrend[]
  top_categories: CategoryAmount[]
  total_income_30d: string
  total_expense_30d: string
}
