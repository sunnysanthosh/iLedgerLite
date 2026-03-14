import { NextResponse } from "next/server"

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

export async function GET() {
  const stagingTotal  = RESOURCES.reduce((s, r) => s + r.stagingMonthly, 0)
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
