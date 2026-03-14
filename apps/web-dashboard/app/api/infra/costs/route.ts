import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// ---------------------------------------------------------------------------
// Cost data derived from live Terraform config (infrastructure/terraform/).
// Upgrade path: replace RESOURCES and SNAPSHOTS with live GCP Billing API
// calls using a service-account key stored in GOOGLE_APPLICATION_CREDENTIALS.
// ---------------------------------------------------------------------------

export interface ResourceCost {
  name: string
  spec: string
  stagingMonthly: number   // USD
  productionMonthly: number | null
}

export interface SprintSnapshot {
  sprint: string
  stagingCost: string
  productionCost: string
  notes: string
  date: string
}

export interface BudgetLine {
  environment: string
  currentEstimate: number
  cap: number
  alertAt: number
}

export interface CostTrend {
  month: string
  staging: number
  production: number | null
}

// Known resource costs from Terraform config — us-central1 pricing
const RESOURCES: ResourceCost[] = [
  { name: "GKE cluster management", spec: "Standard zonal, 1 cluster", stagingMonthly: 0, productionMonthly: 73 },
  { name: "GKE nodes", spec: "3× preemptible e2-medium / 2× e2-standard-2", stagingMonthly: 30, productionMonthly: 130 },
  { name: "Cloud SQL", spec: "db-f1-micro 20GB / db-custom-2-7680 50GB REGIONAL", stagingMonthly: 15, productionMonthly: 195 },
  { name: "Memorystore Redis", spec: "None in staging / STANDARD_HA 2GB", stagingMonthly: 0, productionMonthly: 90 },
  { name: "Network Load Balancer", spec: "1 forwarding rule / HTTPS LB", stagingMonthly: 18, productionMonthly: 25 },
  { name: "Cloud NAT", spec: "Not used in staging / Private GKE nodes", stagingMonthly: 0, productionMonthly: 32 },
  { name: "Cloud Storage", spec: "Receipts bucket ~0GB dev / ~10GB prod", stagingMonthly: 1, productionMonthly: 5 },
  { name: "VPC / Cloud Router", spec: "Router + negligible egress", stagingMonthly: 7, productionMonthly: 15 },
]

const BUDGETS: BudgetLine[] = [
  { environment: "Staging",    currentEstimate: 49,  cap: 150, alertAt: 120 },
  { environment: "Production", currentEstimate: 0,   cap: 650, alertAt: 520 },
]

// Sprint-exit snapshots — appended by FT-02 cost-snapshot.yml CI job
const SNAPSHOTS: SprintSnapshot[] = [
  { sprint: "Sprint 11", stagingCost: "~$71–144/mo", productionCost: "—", notes: "No new GCP resources", date: "2026-03-02" },
  { sprint: "Sprint 12", stagingCost: "~$49/mo",     productionCost: "—", notes: "On-demand stop/start active (TD-33)", date: "2026-03-09" },
]

// 3-month trend (estimated from resource changes across sprints)
const TRENDS: CostTrend[] = [
  { month: "Jan 2026", staging: 0,   production: null },
  { month: "Feb 2026", staging: 107, production: null },  // Sprint 10 — always-on
  { month: "Mar 2026", staging: 49,  production: null },  // Sprint 12 — nightly-off model
]

// ---------------------------------------------------------------------------
// Server-side admin check
// Uses AUTH_URL (server-only env var, no NEXT_PUBLIC_ prefix) to call
// auth-service /auth/me. Falls back to NEXT_PUBLIC_AUTH_URL for local dev.
//
// Admin access granted when EITHER condition is true:
//   1. auth-service returns { is_admin: true } (future backend field)
//   2. user email is in ADMIN_EMAILS env var (server-only, comma-separated)
//
// Fails closed on network error or timeout — no data is returned.
// ---------------------------------------------------------------------------

async function resolveAdminStatus(token: string): Promise<boolean> {
  const authBase =
    process.env.AUTH_URL ??
    process.env.NEXT_PUBLIC_AUTH_URL ??
    "http://localhost:8001"

  let userEmail: string
  let isAdminFlag: boolean

  try {
    const res = await fetch(`${authBase}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return false
    const user = (await res.json()) as { email?: string; is_admin?: boolean }
    if (!user.email) return false
    userEmail = user.email
    isAdminFlag = user.is_admin === true
  } catch {
    return false  // network error or timeout — deny access
  }

  if (isAdminFlag) return true

  // Server-side allow-list: ADMIN_EMAILS (no NEXT_PUBLIC_ — stays server-only)
  const allowList = process.env.ADMIN_EMAILS ?? ""
  if (!allowList) return false

  return allowList
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .includes(userEmail.toLowerCase())
}

export async function GET(request: NextRequest) {
  // ── 1. Require Bearer token ──────────────────────────────────────────────
  const authHeader = request.headers.get("authorization")
  if (!authHeader?.startsWith("Bearer ")) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  const token = authHeader.slice(7)

  // ── 2. Verify token + admin role (server-side, via auth-service) ─────────
  const admin = await resolveAdminStatus(token)
  if (!admin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 })
  }

  // ── 3. Return cost data ──────────────────────────────────────────────────
  const stagingTotal    = RESOURCES.reduce((s, r) => s + r.stagingMonthly, 0)
  const productionTotal = RESOURCES.reduce((s, r) => s + (r.productionMonthly ?? 0), 0)

  return NextResponse.json({
    resources: RESOURCES,
    budgets: BUDGETS,
    snapshots: SNAPSHOTS,
    trends: TRENDS,
    totals: { staging: stagingTotal, production: productionTotal },
    note: "Costs derived from Terraform config. Upgrade to live GCP Billing API by setting GOOGLE_APPLICATION_CREDENTIALS.",
  })
}
