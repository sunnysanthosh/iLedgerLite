# LedgerLite — Product & Engineering Roadmap

> **RICE scoring:** Reach (1–10 users/systems affected) × Impact (0.25/0.5/1/2/3) × Confidence (%) ÷ Effort (weeks)
> Higher score = do first. Last updated: 2026-03-22 after Sprint 14.

---

## Current State — Sprint 14 Done ✅ (tagged `sprint-14-done`)

| Component | Status | Details |
|---|---|---|
| **auth-service** | ✅ Done | 4 endpoints, 15 tests; org membership eager-load in /me |
| **user-service** | ✅ Done | 12 endpoints (5 user + 7 org CRUD), 30 tests |
| **transaction-service** | ✅ Done | 12 endpoints, 27 tests; org_id scoped |
| **ledger-service** | ✅ Done | 7 endpoints, 26 tests; org_id scoped |
| **report-service** | ✅ Done | 5 endpoints, 18 tests; org_id scoped |
| **notification-service** | ✅ Done | 3 endpoints, 12 tests |
| **ai-service** | ✅ Done | 3 endpoints, 16 tests |
| **sync-service** | ✅ Done | 3 endpoints, 14 tests |
| **database** | ✅ Done | schema.sql, 5 Alembic migrations, 29 seed categories, organisations + org_memberships tables |
| **CI/CD** | ✅ Done | test + lint + build (GHCR + Trivy) + deploy (smoke + rollback) + terraform-lint + 60% coverage gate + Slack alerts |
| **apps/mobile-app** | ✅ Done | Flutter — 6 screens, 43 Dart files, offline sync, cert pinning |
| **apps/web-dashboard** | ✅ Done | Next.js 14 — 6 tabs + admin infra tab, TypeScript, Recharts |
| **infrastructure/kubernetes** | ✅ Done | Kustomize base + staging/production overlays; PDB, HPA, ResourceQuota, TLS, NetworkPolicies |
| **infrastructure/terraform** | ✅ Done | 6 GCP modules (VPC, GKE, CloudSQL, Memorystore, Storage, IAM) |
| **GCP staging** | ✅ Live | All 8 services running in `ledgerlite-staging`, 5 migrations applied |
| **multi-user orgs** | ✅ Done | Backend complete (organisations + org_memberships, `get_org_member`, org CRUD, org_id scoping all data services); web/mobile UI → Sprint 15 |

**158 tests passing. GCP staging live. main at `sprint-14-done` (`abf6392`).**

---

## Cloud Cost Baseline

> Reviewed and recorded at every sprint exit. Costs derived from live terraform config (us-central1).
> Last reviewed: Sprint 11 exit, 2026-03-02.

### Staging — Live Today (always-on model)

| Resource | Spec | Monthly Est. |
|---|---|---|
| GKE cluster management | Standard zonal, 1 cluster | $0–$73 ¹ |
| GKE nodes | 3 × preemptible e2-medium (2vCPU/4GB), 50GB pd-standard | $30 |
| Cloud SQL | db-f1-micro, PD-SSD 20GB, ZONAL, 7-day backups | $15 |
| Network Load Balancer | nginx-ingress → GCP Network LB (1 forwarding rule) | $18 |
| Cloud Storage | receipts bucket, ~0 GB at dev stage | $1 |
| VPC / Cloud Router | Router + negligible intra-VPC egress | $7 |
| **TOTAL STAGING (always-on)** | | **$71–$144 / month** |

> ¹ GCP waives the $73/month cluster management fee for the first zonal cluster per billing account — verify in GCP Billing console.

### Staging — On-Demand Model (TD-33, implemented Sprint 12)

Scale GKE nodes to 0 + stop Cloud SQL when not in use. Start/stop via GitHub Actions.
Fixed costs (LB $18, Router $7, Storage $1) are unavoidable regardless of on/off.

| Scenario | Active hrs/month | Compute cost | Fixed | **Total** | **vs always-on** |
|---|---|---|---|---|---|
| Always-on | 730 hrs | $45 | $26 | **$71** | baseline |
| Business hours (8 hrs/day) | ~240 hrs | $15 | $26 | **$41** | **−$30/mo** |
| CI-builds-only (~3 hrs/day) | ~90 hrs | $6 | $26 | **$32** | **−$39/mo** |
| Nightly off only (16 hrs off) | ~360 hrs | $23 | $26 | **$49** | **−$22/mo** |

> **Chosen approach (nightly schedule):** Stop every night at 10 PM UTC (3:30 AM IST) via `staging-stop.yml` cron. Restart manually or before a deploy via `staging-start.yml`. No wasted overnight compute.

### Production — Projected (not yet deployed)

| Resource | Spec | Monthly Est. |
|---|---|---|
| GKE cluster management | Standard regional, 1 cluster | $73 |
| GKE nodes | 2 × on-demand e2-standard-2 (4vCPU/16GB), 50GB pd-standard | $130 |
| Cloud SQL | db-custom-2-7680 (2vCPU/7.5GB), PD-SSD 50GB, REGIONAL, PITR | $195 |
| Memorystore Redis | STANDARD_HA 2GB, Redis 7 | $90 |
| HTTP(S) Load Balancer | with HTTPS offload + cert | $25 |
| Cloud NAT | for private GKE nodes | $32 |
| Cloud Storage | receipts bucket, ~10GB/month | $5 |
| VPC / Cloud Router | Router + inter-zone egress | $15 |
| **TOTAL PRODUCTION** | | **~$565 / month** |

### Budget Caps + Alert Thresholds

| Environment | Current Spend | Monthly Cap | Alert at |
|---|---|---|---|
| Staging | ~$71–144 / mo | **$150** | $120 (80%) |
| Production | Not live | **$650** | $520 (80%) |
| Combined cap | ~$71–144 / mo | **$800** | $640 (80%) |

> Action (Sprint 12 — TD-32): Configure GCP Budget Alerts in console immediately. 15 minutes, prevents surprise bills.

### Sprint-Exit Cost Snapshot

| Sprint | Staging Cost | Production Cost | Notes |
|---|---|---|---|
| Sprint 10 | ~$71–144/mo | — | GCP staging first deployed |
| Sprint 11 | ~$71–144/mo | — | No new GCP resources added |
| Sprint 12 | TBD (~$32–49/mo) | — | Budget Alerts (TD-32) + on-demand stop/start (TD-33) |
| Sprint 13 | TBD | — | Admin cost dashboard live (FT-01) |

---

## Tech Debt Backlog — RICE Prioritised

> RICE = (Reach × Impact × Confidence) ÷ Effort
> R: 1–10 users/systems · I: 0.25 minimal / 0.5 low / 1 medium / 2 high / 3 massive · C: % confidence · E: weeks

### Tier 1 — Must Fix Before Production (Score ≥ 20)

| ID | Item | Layer | R | I | C | E | Score | Sprint |
|---|---|---|---|---|---|---|---|---|
| TD-01 | Add KUBECONFIG secret to GitHub — deploy.yml is non-functional without it | CI/CD | 6 | 2 | 1.0 | 0.1 | **120** | S11 |
| TD-02 | Fix `kubectl --record` deprecation in deploy.yml:71 | CI/CD | 5 | 1 | 1.0 | 0.1 | **50** | S11 |
| TD-03 | ResourceQuota on namespace — rogue workload can starve cluster | K8s | 5 | 2 | 1.0 | 0.2 | **50** | S11 |
| TD-04 | Scale all services to replicas: 2 — eliminate single-pod outages | K8s | 9 | 2 | 1.0 | 0.5 | **36** | S11 |
| TD-05 | TLS/HTTPS on Ingress — all traffic plain HTTP today | K8s | 9 | 3 | 1.0 | 1.0 | **27** | S11 |
| TD-06 | PodDisruptionBudgets — node drain can wipe all pods simultaneously | K8s | 7 | 2 | 0.9 | 0.5 | **25** | S11 |
| TD-13 | Trivy container vulnerability scanning in build.yml | CI/CD | 6 | 2 | 0.9 | 0.5 | **22** | S11 |
| TD-07 | Smoke tests after deploy — catch broken deploys before they impact users | CI/CD | 7 | 2 | 1.0 | 1.0 | **14** | S11 |
| TD-08 | Auto-rollback on failed smoke test | CI/CD | 7 | 2 | 0.8 | 1.0 | **11** | S11 |
| TD-09 | HorizontalPodAutoscaler (CPU 50% → scale 1–4 replicas) on all services | K8s | 8 | 2 | 0.9 | 1.5 | **10** | S11 |
| TD-10 | Kubernetes NetworkPolicies — east-west traffic fully open today | K8s | 8 | 3 | 0.8 | 2.0 | **10** | S13 |

### Tier 2 — High Priority (Score 5–20)

| ID | Item | Layer | R | I | C | E | Score | Sprint |
|---|---|---|---|---|---|---|---|---|
| TD-11 | Mobile: remove hardcoded localhost fallback URLs in api_constants.dart | Mobile | 7 | 2 | 1.0 | 0.5 | **28** | S12 |
| TD-12 | Web: remove hardcoded localhost fallback URLs in lib/api/client.ts | Web | 6 | 2 | 1.0 | 0.5 | **24** | S12 |
| TD-14 | CORS middleware on all 8 FastAPI services | Backend | 8 | 3 | 0.9 | 1.0 | **22** | S12 |
| TD-15 | Idempotent seed migration 002 (ON CONFLICT DO NOTHING) | DB | 5 | 2 | 1.0 | 0.5 | **20** | S12 |
| TD-16 | Missing FK indexes: transactions.category_id, notifications.is_read, customers.email | DB | 7 | 2 | 1.0 | 1.0 | **14** | S12 |
| TD-17 | Redis: convert to StatefulSet + PVC (1Gi) — data lost on pod restart | K8s | 7 | 2 | 0.9 | 1.0 | **13** | S12 |
| TD-18 | pytest-cov + coverage report artifact in test.yml | CI/CD | 5 | 1 | 1.0 | 0.5 | **10** | S11 |
| TD-23 | Log error context in db/session.py except handler (all 8 services) | Backend | 4 | 1 | 1.0 | 0.5 | **8** | S12 |
| TD-24 | Terraform lint in CI (terraform validate + fmt check) | Terraform | 3 | 1 | 1.0 | 0.5 | **6** | S11 |
| TD-19 | Rate limiting middleware (slowapi — 100 req/min per IP) on all services | Backend | 8 | 2 | 0.8 | 2.0 | **6** | S12 |
| TD-20 | Alembic downgrade() functions for migrations 001 + 002 | DB | 4 | 2 | 0.8 | 1.0 | **6** | S12 |

### New Feature Backlog — Operator / Admin

> Operator-facing features for the founding team. RICE scored on business impact, not user reach.

| ID | Item | Layer | R | I | C | E | Score | Sprint |
|---|---|---|---|---|---|---|---|---|
| TD-32 | GCP Budget Alerts (staging $120 warn, production $520 warn) — 15 min setup in console | Infra | 5 | 2 | 1.0 | 0.1 | **100** | S12 |
| TD-33 | On-demand staging: `staging-start.yml` + `staging-stop.yml` (nightly cron) + CI SA terraform — saves ~$22–39/mo | CI/CD | 4 | 2 | 0.9 | 0.5 | **14.4** | S12 |
| FT-02 | Sprint-exit cost snapshot — GitHub Actions job captures `gcloud billing` at sprint tag time | CI/CD | 3 | 1 | 0.9 | 0.3 | **9** | S12 |
| FT-01 | Admin cost dashboard — new "Infra" tab in Next.js web dashboard; GCP Billing API breakdown by resource, 3-month trend chart, budget vs actual, cost-per-active-user, sprint-exit snapshot history | Web | 2 | 3 | 0.8 | 0.5 | **9.6** | S13 |

### Tier 3 — Quality / DX (Score < 5)

| ID | Item | Layer | R | I | C | E | Score | Sprint |
|---|---|---|---|---|---|---|---|---|
| TD-27 | Fix kustomize `commonLabels` deprecation warning on every apply | K8s | 2 | 0.5 | 1.0 | 0.2 | **5** | S11 |
| TD-22 | Image digest pinning (sha256) instead of :latest in kustomization | K8s | 6 | 1 | 0.9 | 1.0 | **5** | S13 |
| TD-26 | Certificate pinning in Flutter HTTPS client | Mobile | 5 | 2 | 0.6 | 2.0 | **3** | S13 |
| TD-28 | Slack/email notification on CI failure | CI/CD | 3 | 0.5 | 1.0 | 0.5 | **3** | S13 |
| TD-25 | Increase test coverage: ai (33%), report (35%), notification (36%) to 60% | Backend | 4 | 1 | 0.9 | 2.0 | **2** | S13 |
| TD-21 | Structured JSON logging + correlation ID middleware across all services | Backend | 6 | 1 | 0.8 | 2.0 | **2** | S13 |
| TD-29 | Deployment + rollback runbooks in docs/runbooks/ | Docs | 3 | 1 | 1.0 | 1.0 | **3** | S14 |
| TD-30 | Incident response runbook in docs/runbooks/ | Docs | 2 | 1 | 1.0 | 1.0 | **2** | S14 |
| TD-31 | Architecture Decision Records (ADRs) for 5 key choices | Docs | 2 | 0.5 | 1.0 | 2.0 | **0.5** | S14 |

---

## Sprint 11 — Production Readiness: HA + TLS + CI Hardening

> **Goal:** Make staging safe enough to show early customers. Close all Tier 1 gaps.
> **Branch:** `sprint-11/production-readiness`

| # | Task | ID | Effort |
|---|---|---|---|
| 1 | Add KUBECONFIG + env secrets to GitHub Actions environments | TD-01 | 0.5d |
| 2 | Remove `--record` from deploy.yml, add `--output` instead | TD-02 | 0.1d |
| 3 | Add ResourceQuota to base namespace manifest | TD-03 | 0.5d |
| 4 | Scale all services to `replicas: 2` in production overlay | TD-04 | 0.5d |
| 5 | Install cert-manager + ClusterIssuer (Let's Encrypt) + TLS on Ingress | TD-05 | 1d |
| 6 | Add PodDisruptionBudget (minAvailable: 1) for all 8 services | TD-06 | 0.5d |
| 7 | Add Trivy vulnerability scan step to build.yml | TD-13 | 0.5d |
| 8 | Add smoke test step to deploy.yml (curl /health all services) | TD-07 | 1d |
| 9 | Add auto-rollback step on smoke test failure | TD-08 | 0.5d |
| 10 | Add HPA manifest (CPU 50%, min 1, max 4) for all services | TD-09 | 1d |
| 11 | Add pytest-cov to test.yml, upload coverage report artifact | TD-18 | 0.5d |
| 12 | Add `terraform fmt -check` and `terraform validate` to lint.yml | TD-24 | 0.5d |
| 13 | Fix kustomize `commonLabels` → `labels` deprecation | TD-27 | 0.2d |

**Sprint 11 deliverables:** HTTPS on staging, all services HA + auto-scaling, every deploy verified, security scanning on every build.

---

## Sprint 12 — Data Reliability + App Correctness + Cost Visibility

> **Goal:** Fix data loss risks, missing indexes, app URL configuration, CORS. Add cost guardrails.
> **Branch:** `sprint-12/data-reliability`

| # | Task | ID | Effort |
|---|---|---|---|
| 1 | Configure GCP Budget Alerts: staging $120 warn + $150 cap; production $520 + $650 | TD-32 | 0.2d |
| 2 | On-demand staging: `staging-start.yml` + `staging-stop.yml` (nightly 10PM UTC cron) + CI SA in Terraform IAM | TD-33 | 0.5d |
| 3 | Sprint-exit cost snapshot: GitHub Actions job records `gcloud billing` totals at tag | FT-02 | 0.5d |
| 4 | Mobile: env-driven API URLs — no hardcoded localhost defaults | TD-11 | 0.5d |
| 5 | Web: env-driven API URLs — no hardcoded localhost defaults | TD-12 | 0.5d |
| 6 | Add CORS middleware to all 8 FastAPI services (origins from config) | TD-14 | 1d |
| 7 | Fix seed migration 002 for idempotency (ON CONFLICT DO NOTHING) | TD-15 | 0.5d |
| 8 | Migration 003: add missing FK indexes to schema | TD-16 | 1d |
| 9 | Redis: StatefulSet + PVC 1Gi + update Deployment → StatefulSet | TD-17 | 1d |
| 10 | Add slowapi rate limiting (100 req/min per IP) to all services | TD-19 | 1d |
| 11 | Write Alembic downgrade() for migrations 001 + 002 | TD-20 | 1d |
| 12 | Add logging to db/session.py except handler (all 8 services) | TD-23 | 0.5d |

**Sprint 12 deliverables:** GCP Budget Alerts live, staging auto-stops nightly (saves ~$22–39/mo), sprint costs recorded automatically, no Redis data loss on restart, correct DB query performance, app works end-to-end in staging, rate limiting active.

---

## Sprint 13 — Security Hardening + Observability + Admin Cost Dashboard

> **Goal:** Lock down cluster network, add structured logging, improve test coverage, launch admin cost dashboard.
> **Branch:** `sprint-13/security-observability`

| # | Task | ID | Effort |
|---|---|---|---|
| 1 | Admin cost dashboard — "Infra" tab in Next.js; GCP Billing API, resource breakdown, 3-mo trend, budget % | FT-01 | 0.5d |
| 2 | Kubernetes NetworkPolicies: deny-all default + explicit service allows | TD-10 | 2d |
| 3 | Image digest pinning: resolve sha256 in CI, write to kustomization | TD-22 | 1d |
| 4 | Structured JSON logging + trace-id request middleware (all services) | TD-21 | 3d |
| 5 | Increase test coverage for ai, report, notification services to 60% | TD-25 | 3d |
| 6 | Certificate pinning in Flutter HTTP client (Dio + custom validator) | TD-26 | 2d |
| 7 | Slack notification on CI failure (GitHub Actions webhook) | TD-28 | 0.5d |

### FT-01 Admin Cost Dashboard — Design Spec

**Location:** New "Infra" tab in the existing Next.js web dashboard (`apps/web-dashboard/`)

**Panels:**

| Panel | Data Source | Refresh |
|---|---|---|
| Current month spend by resource | GCP Billing API `projects.billingInfo` + cost export | On load |
| Staging vs production breakdown | Billing label filter: `environment=staging/production` | On load |
| 3-month spend trend chart (Recharts LineChart) | Billing cost export → BigQuery or direct API | On load |
| Budget vs actual (progress bars) | Hardcoded caps from env vars vs API actuals | On load |
| Cost-per-active-user (once users exist) | Billing total ÷ user-service count API | On load |
| Sprint-exit snapshots table | Static JSON generated by FT-02 CI job | On load |

**Access:** Admin-only route (`/infra`), gated by `user.role === 'admin'` claim in JWT.

**API:** New `GET /api/infra/costs` endpoint in Next.js API routes — proxies GCP Billing API with service-account credentials (not exposed to browser).

**Sprint 13 deliverables:** Admin cost dashboard live, zero implicit pod-to-pod access, full request tracing, hardened mobile client.

---

## Sprint 14 — Help Centre + Documentation Hub

> **Goal:** Internal runbooks for the team + external user docs for customers. Foundation for future video guides.
> **Branch:** `sprint-14/help-centre`

### 14A. Internal Documentation (Team-facing)

| Document | Path | Priority | RICE |
|---|---|---|---|
| Deployment runbook | `docs/runbooks/DEPLOY.md` | P1 | 12 |
| Rollback runbook | `docs/runbooks/ROLLBACK.md` | P1 | 10 |
| Incident response playbook | `docs/runbooks/INCIDENT.md` | P1 | 8 |
| Secrets rotation guide | `docs/runbooks/SECRETS.md` | P1 | 8 |
| Environment variables reference | `docs/ENV-VARS.md` | P1 | 7 |
| Contributing guide | `docs/CONTRIBUTING.md` | P2 | 5 |
| ADR 001: Microservices vs monolith | `docs/adr/001-microservices.md` | P2 | 2 |
| ADR 002: PostgreSQL + Redis choices | `docs/adr/002-postgresql-redis.md` | P2 | 2 |
| ADR 003: Flutter over React Native | `docs/adr/003-flutter-first.md` | P2 | 2 |
| ADR 004: Kustomize over Helm | `docs/adr/004-kustomize.md` | P2 | 2 |
| ADR 005: GCP over AWS | `docs/adr/005-gcp-gke.md` | P2 | 2 |

### 14B. External User Documentation (Customer-facing)

Hosted on Docusaurus 3 at `docs/help-centre/`, deployed to GitHub Pages.

#### Getting Started

| Article | Audience | RICE |
|---|---|---|
| What is LedgerLite? | All | 9 |
| Creating your account (register + onboarding) | All | 9 |
| Personal vs Business account type | All | 8 |
| Setting currency and language | All | 7 |
| Installing the mobile app (Android) | Mobile users | 8 |
| Using the web dashboard | Web users | 7 |

#### Feature Guide — Transactions

| Article | Audience |
|---|---|
| Adding your first transaction | All |
| Income vs Expense vs Transfer | All |
| Using and creating categories | All |
| Filtering and searching transactions | All |
| Editing and deleting transactions | All |
| Exporting transactions to CSV | All |

#### Feature Guide — Accounts

| Article | Audience |
|---|---|
| Creating accounts (cash, bank, wallet, credit card) | All |
| Understanding account balances | All |
| Managing multiple accounts | All |
| Transfers between accounts | All |

#### Feature Guide — Business Ledger (Udhar Bahi)

| Article | Audience |
|---|---|
| What is the Business Ledger? | Business users |
| Adding a customer | Business users |
| Recording credit given (debit entry) | Business users |
| Recording payment received (credit entry) | Business users |
| Settling an account — full and partial | Business users |
| Sending a payment reminder | Business users |
| Understanding outstanding balance calculation | Business users |

#### Feature Guide — Reports

| Article | Audience |
|---|---|
| Profit & Loss report explained | All |
| Cashflow report: daily / weekly / monthly | All |
| Budget vs actual spending by category | All |
| Dashboard summary — what the numbers mean | All |
| Exporting your reports | All |

#### Feature Guide — Settings

| Article | Audience |
|---|---|
| Editing your profile | All |
| Changing your display currency | All |
| Notification preferences (push + email) | All |
| Offline sync — how it works, manual sync | Mobile users |
| Logging out safely | All |

#### Troubleshooting + FAQ

| Article |
|---|
| My balance looks wrong |
| I can't log in / forgot password |
| Data not syncing on mobile |
| How is my data kept secure? |
| Can I use LedgerLite offline? |
| How do I delete my account? |

### 14C. Video Guide Plan (record after text content approved)

| Video | Length | Priority |
|---|---|---|
| LedgerLite in 2 minutes — overview | 2 min | P1 |
| Getting started: your first transaction | 3 min | P1 |
| Business Ledger walkthrough (shop owner) | 4 min | P1 |
| Reading your reports | 3 min | P2 |
| Setting up offline sync on mobile | 2 min | P2 |
| Advanced: data export and management | 3 min | P3 |

### 14D. Help Centre Tech Stack

```
docs/help-centre/
  docs/
    getting-started/
    transactions/
    accounts/
    ledger/
    reports/
    settings/
    troubleshooting/
  blog/               ← release notes, feature announcements
  docusaurus.config.ts
  sidebars.ts
```

**Hosting:** GitHub Pages (free, auto-deploy on push to main)
**Fallback:** Vercel (preview deploys per PR)

---

## User Experience Features Map

### Currently Shipped

| Feature | Mobile | Web | API | Notes |
|---|---|---|---|---|
| Register / Login / Logout | ✅ | ✅ | ✅ | JWT, bcrypt, refresh token rotation |
| Auto token refresh | ✅ | ✅ | ✅ | Interceptor-based |
| Profile view + edit | ✅ | ✅ | ✅ | Name, phone, business name |
| Onboarding flow | ✅ | ✅ | ✅ | Account type, currency, language |
| Notification settings | ✅ | ✅ | ✅ | Push + email toggles |
| Dashboard — balance overview | ✅ | ✅ | ✅ | Total, income, expenses |
| Dashboard — recent transactions | ✅ | ✅ | ✅ | Last 5 |
| Accounts — create / list / edit | ✅ | ✅ | ✅ | Cash, bank, wallet, credit card |
| Account balance auto-tracking | ✅ | ✅ | ✅ | Updated on every transaction |
| Transactions — add / edit / delete | ✅ | ✅ | ✅ | Amount, category, date, notes |
| Transactions — filter / search | ✅ | ✅ | ✅ | Date range, type, category, account |
| Transactions — pagination | ✅ | ✅ | ✅ | |
| Categories — 29 system defaults | ✅ | ✅ | ✅ | 8 income + 21 expense |
| Categories — custom create | ✅ | ✅ | ✅ | Per user, income or expense |
| Business Ledger — customer CRUD | ✅ | ✅ | ✅ | Name, phone, email, address |
| Business Ledger — debit / credit entries | ✅ | ✅ | ✅ | With due date |
| Business Ledger — settlement | ✅ | ✅ | ✅ | Full + partial payment |
| Business Ledger — outstanding balance | ✅ | ✅ | ✅ | Real-time aggregation |
| Reports — P&L | ✅ | ✅ | ✅ | Revenue, expenses, net |
| Reports — Cashflow | ✅ | ✅ | ✅ | Daily / weekly / monthly buckets |
| Reports — Budget breakdown | ✅ | ✅ | ✅ | Category spending |
| Reports — Summary dashboard | ✅ | ✅ | ✅ | Aggregate stats |
| Reports — CSV Export | ✅ | ✅ | ✅ | Date-range filtered download |
| AI — Category suggestion | 🔶 | 🔶 | ✅ | Rule-based (not ML) |
| AI — Spending insights | 🔶 | 🔶 | ✅ | Statistical anomaly detection |
| AI — Receipt OCR | 🔶 | 🔶 | ✅ | Returns mock data (real impl deferred) |
| Notifications — list / mark read | ✅ | ✅ | ✅ | |
| Notifications — credit reminder | ✅ | ✅ | ✅ | Trigger per customer |
| Offline mode (SQLite mirror) | ✅ | N/A | ✅ | Local transaction/ledger copy |
| Background sync | ✅ | N/A | ✅ | Automatic push/pull cycle |
| Manual sync trigger | ✅ | N/A | ✅ | From settings screen |
| Dark mode | ✅ | 🔲 | N/A | Flutter Material 3 |
| Help Centre | 🔲 | 🔲 | N/A | Sprint 14 |

Legend: ✅ Done · 🔶 Stub/partial · 🔲 Planned · N/A Not applicable

### Planned — Phase 2 (Month 5–8)

| Feature | Mobile | Web | API | RICE est. | Notes |
|---|---|---|---|---|---|
| OTP / phone login | 🔲 | 🔲 | 🔲 | High | MSG91 / Firebase, India market |
| Password reset via email | 🔲 | 🔲 | 🔲 | High | SMTP + magic link |
| Bank SMS auto-import | 🔲 | N/A | 🔲 | High | Parse Axis/HDFC/SBI SMS format |
| UPI reference tracking | 🔲 | 🔲 | 🔲 | High | Log UPI transaction IDs |
| WhatsApp credit reminders | 🔲 | 🔲 | 🔲 | High | WhatsApp Business API |
| GST-ready tax reports | 🔲 | 🔲 | 🔲 | High | Required for Indian businesses |
| Budget planner + alerts | 🔲 | 🔲 | 🔲 | Medium | Set per-category limits, alert at 80% |
| Multi-language (Hindi, Tamil, Telugu) | 🔲 | 🔲 | N/A | Medium | Flutter l10n + i18n |
| Real Receipt OCR | 🔲 | 🔲 | 🔲 | Medium | Google Vision or Tesseract |
| Voice transaction entry | 🔲 | N/A | 🔲 | Medium | "Add 500 rupees groceries" |
| Family / shared household ledger | 🔲 | 🔲 | 🔲 | Medium | Multi-user single account |
| AI categorization (ML model) | 🔲 | 🔲 | 🔲 | Low | sklearn or Vertex AI |
| Cashflow forecasting | 🔲 | 🔲 | 🔲 | Low | 30-day prediction |
| Help Centre in-app links | 🔲 | 🔲 | N/A | Medium | Contextual "?" → relevant article |

### Planned — Phase 3 (Month 9–18)

| Feature | Mobile | Web | API | Notes |
|---|---|---|---|---|
| Multi-user RBAC | 🔲 | 🔲 | 🔲 | Owner, accountant, view-only |
| Accountant access portal | N/A | 🔲 | 🔲 | Web-only for CA/accountant |
| PDF reports | 🔲 | 🔲 | 🔲 | WeasyPrint / reportlab |
| Advanced analytics | N/A | 🔲 | 🔲 | Cohort analysis, trend detection |
| iOS App Store release | 🔲 | N/A | N/A | Apple Developer account required |
| Public API + API keys | N/A | N/A | 🔲 | For third-party integrations |
| Webhooks | N/A | N/A | 🔲 | Push events to external systems |
| Multi-currency accounts | 🔲 | 🔲 | 🔲 | Exchange rate API |
| White-label option | N/A | 🔲 | 🔲 | B2B: custom branding |

### Planned — Phase 4 (Year 2)

| Feature | Notes |
|---|---|
| In-app UPI / card payments | Razorpay integration |
| Working capital credit | NBFC partnership |
| BNPL for small businesses | Invoice-based credit |
| Insurance recommendations | Based on income/expense patterns |
| Supplier payment management | Track payables |
| Open Banking (AA framework) | Account aggregation, RBI-compliant |

---

## Sprint History

| Sprint | Theme | Status | Tag |
|---|---|---|---|
| Sprint 0 | Auth service | ✅ Done | `sprint-0-done` |
| Sprint 1 | User service + shared foundations | ✅ Done | `sprint-1-done` |
| Sprint 2 | Transaction service | ✅ Done | `sprint-2-done` |
| Sprint 3 | Ledger service | ✅ Done | `sprint-3-done` |
| Sprint 4 | Reports + notifications | ✅ Done | `sprint-4-done` |
| Retro 4.5 | Hardening + CI/CD | ✅ Done | `retro-4.5-done` |
| Sprint 5 | Sync + AI | ✅ Done | `sprint-5-done` |
| Sprint 6A | Alembic migrations | ✅ Done | `sprint-6a-done` |
| Sprint 6B | Kubernetes manifests (Kustomize) | ✅ Done | `sprint-6b-done` |
| Sprint 6C | Terraform IaC for GCP | ✅ Done | `sprint-6c-done` |
| Sprint 7 | Flutter app — auth, dashboard, transactions, accounts | ✅ Done | `sprint-7-done` |
| Sprint 8 | Flutter — ledger, reports, offline sync, settings | ✅ Done | `sprint-8-done` |
| Sprint 9 | Next.js web dashboard (6 tabs) | ✅ Done | `sprint-9-done` |
| Sprint 10 | GCP staging deploy — all 8 services live | ✅ Done | `sprint-10-done` |
| Sprint 11 | HA + TLS + CI hardening (13 tech-debt items) | ✅ Done | `sprint-11-done` |
| Sprint 12 | Data reliability + app correctness + cost visibility | ✅ Done | `sprint-12-done` |
| Sprint 13 | Security hardening + observability + admin cost dashboard + RBAC | ✅ Done | `sprint-13-rbac-baseline` |
| **Sprint 14** | **Multi-user organisations (backend)** | ✅ Done | `sprint-14-done` |
| Sprint 15 | Org switching UI (web + mobile) | 🔲 Next | — |
| Phase 2 | Growth features | 🔲 | — |
| Phase 3 | Scale + platform | 🔲 | — |
| Phase 4 | Embedded finance | 🔲 | — |

---

## System Architecture (Current)

```
┌─────────────────┐   ┌─────────────────┐
│  Flutter Mobile  │   │  Next.js Web    │
│  (Android/iOS)   │   │   Dashboard     │
└────────┬────────┘   └────────┬────────┘
         └──────────┬──────────┘
                    ▼
         ┌──────────────────────┐
         │  nginx Ingress       │  ← TLS (Sprint 11)
         │  GKE LoadBalancer    │
         └──────────┬───────────┘
                    │  path-based routing (/auth, /users, /transactions, ...)
    ┌───────────────┼───────────────────────────┐
    ▼               ▼               ▼            ▼
:8001           :8002           :8003         :8004
Auth            User         Transaction    Ledger
Service         Service        Service      Service
    ▼               ▼               ▼            ▼
:8005           :8006           :8007         :8008
Report           AI          Notification    Sync
Service         Service        Service      Service
    │               │               │            │
    └───────────────┴───────────────┴────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                            ▼
     PostgreSQL 16                     Redis 7
     Cloud SQL                   (cache + JWT blacklist
     10.82.0.3 (private)          + session state)
```
