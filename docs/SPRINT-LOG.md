# Sprint Log

This document tracks all completed and in-progress sprints for the LedgerLite project.

---

## Sprint 0 — Auth Service (Completed)

**Goal:** Implement JWT-based authentication for the platform.

**Delivered:**
- JWT-based registration, login, token refresh, and profile retrieval
- Security hardened with bcrypt password hashing
- Access and refresh JWT tokens with a `type` claim to distinguish token purpose
- Single-use refresh token rotation enforced via Redis (used tokens are blacklisted)
- Anti-enumeration protection: identical error messages returned for wrong password and nonexistent email, preventing user discovery attacks

**Endpoints:**

| Method | Path             | Status | Description                  |
|--------|------------------|--------|------------------------------|
| POST   | /auth/register   | 201    | Register a new user          |
| POST   | /auth/login      | 200    | Login and receive tokens     |
| GET    | /auth/me         | 200    | Get current user profile     |
| POST   | /auth/refresh    | 200    | Refresh token pair           |

**Tests:** 15 passing

---

## Sprint 1 — User Service + Shared Foundations (Completed)

**Goal:** Build user profile management, onboarding flow, user settings, and establish shared cross-service foundations.

**Delivered:**
- User profile management with get, update, and soft-delete
- Onboarding endpoint capturing initial user preferences (can only be called once per user)
- User settings management (notifications, language, currency)
- Added `user_settings` table to `database/schema.sql`
- Created `shared/` module providing reusable cross-service utilities:
  - `base_settings` — common configuration via Pydantic settings
  - `pagination` — standardized pagination helpers
  - `auth` — JWT verification and dependency injection utilities

**Endpoints:**

| Method | Path                    | Status | Description                        |
|--------|-------------------------|--------|------------------------------------|
| GET    | /users/me               | 200    | Get profile with settings          |
| PUT    | /users/me               | 200    | Update profile fields              |
| POST   | /users/me/onboarding    | 200    | Complete onboarding (one-time)     |
| PUT    | /users/me/settings      | 200    | Update user settings               |
| DELETE | /users/me               | 200    | Deactivate account (soft delete)   |

**Onboarding captures:**
- `account_type` — personal, business, or both
- `currency` — user's preferred currency (e.g., INR)
- `language` — user's preferred language (e.g., en)
- `business_category` — optional, relevant for business accounts

**Settings:**
- `notifications_enabled` — toggle push/email notifications
- `language` — display language
- `currency` — default currency for transactions

**Tests:** 18 passing

**Key Technical Decision:** Used `populate_existing=True` when merging SQLAlchemy model instances to solve an async identity map caching issue. Without this flag, the async session would return stale objects from its identity map instead of reflecting freshly committed database state.

---

## Sprint 2 — Transaction Service (Completed)

**Goal:** Implement the core finance engine — transaction CRUD, account management, and category management.

**Delivered:**
- Full account management: create, list, get, update, deactivate (5 endpoints)
- Category management: create custom categories, list with type filter, system categories seed data (2 endpoints)
- Transaction CRUD with automatic account balance updates on create, update, and delete (5 endpoints)
- Pagination support on transaction listing (skip/limit with total count)
- Multi-filter transaction queries: by account, category, type, date range
- Balance recalculation: income adds, expense subtracts; reversals on update/delete
- Seed data: 29 system categories (8 income + 21 expense) in `database/seeds/categories.sql`

**Endpoints:**

| Method | Path                       | Status | Description                                |
|--------|----------------------------|--------|--------------------------------------------|
| POST   | /accounts                  | 201    | Create account (cash, bank, wallet, etc.)  |
| GET    | /accounts                  | 200    | List user's active accounts                |
| GET    | /accounts/{id}             | 200    | Get account detail with balance            |
| PUT    | /accounts/{id}             | 200    | Update account name/type                   |
| DELETE | /accounts/{id}             | 200    | Deactivate account                         |
| POST   | /categories                | 201    | Create custom category                     |
| GET    | /categories                | 200    | List categories (system + user, filterable)|
| POST   | /transactions              | 201    | Create transaction (updates balance)       |
| GET    | /transactions              | 200    | List with filters + pagination             |
| GET    | /transactions/{id}         | 200    | Get single transaction                     |
| PUT    | /transactions/{id}         | 200    | Update transaction (adjusts balance)       |
| DELETE | /transactions/{id}         | 200    | Delete transaction (reverses balance)      |

**Tests:** 27 passing (8 accounts + 5 categories + 14 transactions)

**Key Technical Decisions:**
- Account balance is maintained as a running total, adjusted on every transaction create/update/delete
- Transactions use `Numeric(15, 2)` for monetary amounts — never float
- System categories (is_system=True, user_id=NULL) are visible to all users alongside their own custom categories
- Transaction deletion is a hard delete (not soft) since the balance reversal must be atomic

---

## Sprint 3 — Ledger Service (Completed)

**Goal:** Customer credit tracking for shop owners — the differentiating feature.

**Delivered:**
- Full customer management: create, list with search + outstanding balance, get detail, update (4 endpoints)
- Ledger entry management: create debit/credit entries, get full credit history with balance summary, mark settled/partial payment (3 endpoints)
- Outstanding balance calculation: aggregates unsettled debit vs credit entries per customer
- Search across customer name, phone, and email
- Pagination on both customer list and ledger history
- Settlement tracking: entries can be marked settled, which excludes them from outstanding balance calculations

**Endpoints:**

| Method | Path                    | Status | Description                                   |
|--------|-------------------------|--------|-----------------------------------------------|
| POST   | /customers              | 201    | Create customer                               |
| GET    | /customers              | 200    | List customers with search + outstanding balance |
| GET    | /customers/{id}         | 200    | Get customer detail with credit summary       |
| PUT    | /customers/{id}         | 200    | Update customer info                          |
| POST   | /ledger-entry           | 201    | Create ledger entry (debit/credit)            |
| GET    | /ledger/{customer_id}   | 200    | Full credit history + balance summary         |
| PUT    | /ledger-entry/{id}      | 200    | Mark settled / partial payment                |

**Tests:** 26 passing (13 customers + 13 ledger)

**Key Technical Decisions:**
- Outstanding balance = sum(unsettled debits) - sum(unsettled credits); settled entries are excluded
- Uses SQLAlchemy `case()` expression (not `func.case()`) for conditional aggregation — `func.case()` is not valid in SQLAlchemy 2.x
- Customer search uses `ilike` for case-insensitive matching across name/phone/email
- Ledger entries are hard records (not soft-deleted) since balance integrity depends on the full history

---

---

## Sprint 4 — Report Service + Notification Service (Completed)

**Goal:** Financial reports and payment reminders.

**Delivered:**
- Report service with 5 endpoints: profit-loss, cashflow, budget breakdown, dashboard summary, CSV export
- Notification service with 3 endpoints: list notifications, mark as read, trigger credit reminders
- Added `notifications` table to `database/schema.sql`
- Report service reads from transaction, account, category, customer, and ledger_entries tables for aggregation
- Notification service calculates outstanding balances and creates reminder notifications for customers with unpaid debts

**Report Service Endpoints (port 8005):**

| Method | Path                  | Status | Description                                    |
|--------|-----------------------|--------|------------------------------------------------|
| GET    | /reports/profit-loss  | 200    | Revenue vs expenses by date range              |
| GET    | /reports/cashflow     | 200    | Inflows/outflows by period (daily/weekly/monthly) |
| GET    | /reports/budget       | 200    | Spending by category for date range            |
| GET    | /reports/summary      | 200    | Dashboard aggregation (balances, top categories, outstanding ledger) |
| GET    | /reports/export       | 200    | CSV export of transactions for date range      |

**Notification Service Endpoints (port 8007):**

| Method | Path                       | Status | Description                              |
|--------|----------------------------|--------|------------------------------------------|
| GET    | /notifications             | 200    | List user's notifications (paginated)    |
| PUT    | /notifications/{id}/read   | 200    | Mark notification as read                |
| POST   | /notifications/reminder    | 201    | Trigger credit reminder for a customer   |

**Tests:** 30 passing (18 report + 12 notification)

**Key Technical Decisions:**
- Report service has read-only copies of all relevant ORM models (User, Transaction, Account, Category, Customer, LedgerEntry) — it queries the shared PostgreSQL DB directly
- Cashflow grouping supports daily, weekly, and monthly periods with dynamic bucket aggregation
- Budget report returns expense breakdown by category (no budget table yet — client-side comparison)
- Export currently supports CSV format; PDF/Excel can be added later with heavier dependencies
- Notification reminder endpoint validates customer ownership and checks for outstanding balance before creating a notification
- Notifications table includes `related_entity_id` for linking to the relevant customer/entry

**Shared Seed Data Migration:**
- report-service and notification-service tests now use `shared/test_data.py` instead of inline fixtures
- Total tests increased from 113 to 116 (report-service gained 3 tests from more comprehensive seed data coverage)
- Fixed UUID round-trip issue on SQLite: notification-service models now use `sqlalchemy.Uuid` (generic cross-dialect type) instead of `postgresql.UUID(as_uuid=True)`, which misinterprets deterministic UUID hex strings as scientific notation on SQLite
- Key pattern: `_id()` helper converts string UUIDs to `uuid.UUID`, flush after each `add()` to prevent batch insert sentinel errors

**Total tests across all services: 116 (15 + 18 + 27 + 26 + 18 + 12)**

---

## Retro 4.5 — Best Practices Hardening (Completed)

**Goal:** Back-port fixes discovered during Sprint 4, align docker-compose env vars, establish CI/CD.

**Delivered:**

### UUID Type Migration (16 model files)
- Replaced `postgresql.UUID(as_uuid=True)` with `sqlalchemy.Uuid` across all 5 remaining services (auth, user, transaction, ledger, report). Notification-service was already fixed in Sprint 4.
- 16 model files updated. All 116 tests pass after migration.
- Root cause: `postgresql.UUID` stores hex without hyphens on SQLite; deterministic UUIDs containing `e` get misinterpreted as scientific notation.

### Docker-Compose Env Var Fix
- Added prefixed env vars matching each service's `env_prefix` (e.g., `AUTH_DATABASE_URL`, `USER_DATABASE_URL`, `TXN_DATABASE_URL`, etc.)
- Added `JWT_SECRET` env var to all 8 service blocks (shared via `${JWT_SECRET:-dev-secret-change-me}`)
- Corrected Redis DB numbers per service convention (auth=0, user=1, txn=2, ledger=3, report=4, ai=5, notification=6, sync=7)

### CI/CD — GitHub Actions + Tooling
- `.github/workflows/test.yml` — per-service test matrix with change detection (dorny/paths-filter)
- `.github/workflows/lint.yml` — ruff check + format check
- `pyproject.toml` — ruff config (Python 3.12 target, line-length 120, E/F/I/W rules)
- `Makefile` — local dev convenience targets (test-all, test-<service>, lint, format)

### Documentation Updates
- CLAUDE.md: added UUID migration rule under General Rules, added CI/CD section
- ROADMAP.md: added Retro 4.5 entry, updated CI/CD status
- MEMORY.md: updated with retro completion context

**Tests:** 116 passing (no regressions — same count as Sprint 4)

---

## Sprint 5 — AI Service + Sync Service (Completed)

**Goal:** AI-powered categorization/insights and offline sync capabilities.

**Delivered:**

### AI Service (port 8006, prefix AI_, Redis DB 5)
- Rule-based keyword categorization with confidence scoring — maps transaction descriptions to 60+ keywords across 30+ categories
- Spending insights with anomaly detection (>50% deviation flagged) and trend analysis (comparing 30-day windows)
- Top category breakdown, income/expense totals
- Mock OCR endpoint (stub returning realistic receipt data, ready for Google Vision/Tesseract integration)
- Read-only copies of Transaction, Category, Account models for direct DB queries

### Sync Service (port 8008, prefix SYNC_, Redis DB 7)
- Push endpoint: batch upload of transactions and ledger entries from mobile devices with last-write-wins conflict resolution (upsert on existing IDs)
- Pull endpoint: download server changes since a given timestamp (delta sync)
- Status endpoint: last sync time, pending change count per device
- SyncLog model tracks every push/pull operation per user+device
- Added `sync_log` table to `database/schema.sql`

**AI Service Endpoints:**

| Method | Path            | Status | Description                                |
|--------|-----------------|--------|--------------------------------------------|
| POST   | /ai/categorize  | 200    | Predict category from description/amount   |
| GET    | /ai/insights    | 200    | Spending anomalies, trends, top categories |
| POST   | /ai/ocr         | 200    | Receipt OCR extraction (mock)              |

**Sync Service Endpoints:**

| Method | Path          | Status | Description                              |
|--------|---------------|--------|------------------------------------------|
| POST   | /sync/push    | 201    | Upload local changes (batch upsert)      |
| GET    | /sync/pull    | 200    | Download changes since timestamp         |
| GET    | /sync/status  | 200    | Last sync time + pending count           |

**Tests:** 30 new (16 ai + 14 sync), total across all 8 services: **146**

**Key Technical Decisions:**
- Categorization uses keyword matching with confidence = (keyword_length / description_length) + 0.3, capped at 0.95
- Insights anomaly detection threshold: 50% deviation between 30-day windows
- Sync uses last-write-wins for conflict resolution — if a pushed transaction ID already exists, it's overwritten
- Pull returns all changes since a timestamp, or all records if no timestamp given
- SyncLog records every push/pull for audit and device tracking
- Pydantic `@field_validator` on pull response schemas to convert `Decimal` → `str` for JSON serialization

---

## Sprint 6 — Database Migrations + CI/CD Build/Deploy (Completed — 6A + 6D)

**Goal:** Production-grade database management and CI/CD build/deploy pipelines. (6B Kubernetes and 6C Terraform deferred.)

**Delivered:**

### 6A. Alembic Migrations (`database/migrations/`)
- Unified Alembic configuration at `database/` with `alembic.ini` and async-capable `env.py`
- `ALEMBIC_DATABASE_URL` environment variable override for different environments
- **Migration 001**: Initial schema — all 10 tables (users, user_settings, accounts, categories, transactions, customers, ledger_entries, receipts, notifications, sync_log), 9 indexes, check constraints for enums
- **Migration 002**: Seed 29 system categories (8 income + 21 expense) with icons, matching `database/seeds/categories.sql`
- Full downgrade support: drop tables in correct FK order, delete seeded categories

### 6D. CI/CD Build & Deploy (`.github/workflows/`)
- **build.yml** — Docker build + push to GitHub Container Registry (GHCR)
  - Triggers on push to `main` when `services/**` changes
  - Change detection: only builds services with modified files
  - Matrix strategy: parallel builds per service
  - Tags images with git SHA and `latest`
  - Uses `docker/build-push-action@v6` with GHCR authentication
- **deploy.yml** — Manual deploy to staging or production
  - `workflow_dispatch` trigger with environment choice (staging/production) and service selection
  - Configures kubectl via `KUBECONFIG` secret
  - Updates Kubernetes deployments with new image tags
  - Includes migration step placeholder and deployment verification

**Alembic Usage:**
```bash
# Run from database/ directory
cd database

# Apply all migrations
alembic upgrade head

# Apply with custom DB URL
ALEMBIC_DATABASE_URL=postgresql://user:pass@host:5432/db alembic upgrade head

# Rollback one step
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

**Key Decisions:**
- Unified Alembic at repo root level (`database/`) rather than per-service, since all services share a single PostgreSQL database
- Seed migration uses `op.bulk_insert` for portable category seeding (no raw SQL with `gen_random_uuid()`)
- Build workflow uses GHCR (no external registry dependency) with GitHub's built-in `GITHUB_TOKEN`
- Deploy workflow is manual (`workflow_dispatch`) to prevent accidental production deployments
- Deploy expects Kubernetes namespaces named `ledgerlite-staging` and `ledgerlite-production`

---

## Sprint 7 — Flutter Mobile App MVP (Completed)

**Goal:** Core mobile experience — login, dashboard, transaction entry, account management.

**Delivered:**

### Project Setup (`apps/mobile-app/`)
- Clean Architecture folder structure: `core/` (api, theme, storage, router, widgets) + `features/` (auth, dashboard, transactions, accounts)
- State management: Riverpod (flutter_riverpod)
- Navigation: go_router with ShellRoute for bottom navigation
- API client: Dio with AuthInterceptor (JWT auto-attach, 401 → token refresh → retry)
- Theme: Material 3 with light/dark mode, LedgerLite brand colors (green primary)
- Secure storage: flutter_secure_storage with Android encrypted shared preferences

### Auth Feature
- Login screen with email/password, form validation, error display
- Registration screen with full name, email, optional phone, password + confirmation
- Auto-login after registration
- Token persistence across app restarts
- Logout with token clearing

### Dashboard Feature
- Balance card showing total balance, income, and expenses
- Quick stats row (account count, transaction count)
- Recent transactions list (last 5) with type-colored icons
- Pull-to-refresh
- Quick-add FAB navigating to add transaction
- Empty state with prompt to add first transaction

### Transaction Feature
- Transaction list with type filter (all/income/expense/transfer)
- Filter chip indicator with clear button
- Add transaction form with:
  - Segmented type selector (income/expense/transfer)
  - Amount input with INR prefix
  - Account dropdown (from API)
  - Category dropdown (filtered by transaction type)
  - Date picker
  - Description field
- Automatic list refresh after adding

### Account Feature
- Account list with type icons, balance display, currency badge
- Add account form with:
  - Name input
  - Type selection via ChoiceChips (cash, bank, credit card, wallet, loan)
  - Currency dropdown (INR, USD, EUR, GBP, SGD, MYR)
- Empty state with prompt to add first account

### Core Widgets
- `AmountText` — formatted currency display with income/expense coloring
- `LoadingOverlay` — semi-transparent loading indicator
- `ShellScreen` — bottom navigation bar (Dashboard, Transactions, Accounts)

**File Count:** 28 Dart source files + pubspec.yaml + analysis_options.yaml

**Key Packages:**
- `flutter_riverpod` — state management
- `dio` — HTTP client
- `go_router` — declarative routing
- `flutter_secure_storage` — encrypted token storage
- `fl_chart` — chart library (available for Sprint 8 reports)
- `intl` — date/number formatting
- `sqflite` — local SQLite (available for Sprint 8 offline sync)

**Key Decisions:**
- Riverpod over Bloc for simpler boilerplate and native async support
- go_router with ShellRoute for persistent bottom navigation across main screens
- API base URLs use `10.0.2.2` (Android emulator localhost alias), configurable via `--dart-define`
- Auth interceptor handles token refresh transparently — no auth logic in feature code
- Category dropdown dynamically filters by selected transaction type
- All monetary amounts displayed as formatted strings with currency symbols

---

## Sprint 8 — Mobile Ledger + Reports + Offline Sync (Completed)

**Goal:** Business ledger on mobile, report viewing, offline sync, and settings.

**Delivered:**

### 8A. Business Ledger Screens (4 screens)
- **Customer list** with real-time search, outstanding balance per customer, color-coded warning indicators for unpaid debts
- **Customer detail** with balance summary card (total owed/paid/outstanding), debit/credit action buttons, ledger entry timeline with chronological history
- **Add customer form** with name, phone, email, address fields
- **Add ledger entry form** with segmented debit/credit selector, amount with INR prefix, description, due date picker (debit only)
- Settlement: full or partial payment via settle dialog with amount input (full settle or enter partial payment amount with validation)

### 8B. Reports Screens (1 screen + 1 widget)
- **Reports screen** with P&L card (income/revenue, expenses, net profit), spending-by-category pie chart, category list with transaction counts
- **Date range picker** bar — filter all reports by custom date range, clear to reset to all-time
- **Report mode toggle** — Personal/Business segmented button; Business mode shows "Revenue" label and business icon
- **Export** with format picker bottom sheet — CSV or PDF export with date range pass-through
- **SpendingChart widget** using `fl_chart` PieChart with 8-color palette and legend (shows up to 6 categories in legend)
- Pull-to-refresh on all report data

### 8C. Offline Sync (2 core files)
- **LocalDatabase** (`core/sync/local_database.dart`) — sqflite-backed local SQLite with 4 tables: transactions, ledger_entries, customers, sync_meta. Tracks sync status per record with `synced` flag.
- **SyncService** (`core/sync/sync_service.dart`) — push-then-pull sync cycle with periodic timer (5-minute interval). Pushes unsynced local changes, pulls remote changes since last sync time. Exposes sync status as a stream for the UI.
- Sync status stream: idle → syncing → done/error, with pending count and last sync time

### 8D. Settings Screen
- **Profile section** with avatar initials, name, email, phone. **Edit button** opens bottom sheet form (full name, phone, business name) with save/loading state.
- **Sync status** with live state indicator (syncing/error/done), pending count, last sync time, manual sync trigger
- **Preferences**: currency picker (INR/USD/EUR/GBP with check mark on current), language picker (English/Hindi/Tamil/Telugu with check mark on current) — both read current values from user profile settings
- **Notifications**: push and email toggles read live values from profile (not hardcoded), persisted via updateSettings API
- **Logout** with confirmation dialog
- App version footer

### Router & Navigation Updates
- Bottom navigation expanded from 3 to 5 tabs: Home, Transactions, Ledger, Reports, Settings
- 6 new routes: `/ledger`, `/ledger/add-customer`, `/ledger/customer/:id`, `/ledger/customer/:id/add-entry`, `/reports`, `/settings`
- Transactions and Accounts grouped under single "Transactions" tab
- `syncBase` constant added to ApiConstants (port 8008)

**File Count:** 43 Dart files total (15 new: 6 ledger, 4 reports, 3 settings, 2 sync)

**Key Decisions:**
- 5-tab bottom nav keeps all major features one tap away
- Sync uses push-then-pull pattern with last-write-wins conflict resolution (mirrors backend sync-service)
- Local SQLite schema mirrors backend tables with added `synced` boolean flag
- Settings screen doubles as sync control panel — user can trigger manual sync and see pending changes
- PieChart shows percentage labels only for slices ≥5% to avoid text overlap

---

## Sprint 6B — Kubernetes Manifests (Completed)

**Goal:** Production-grade Kubernetes manifests using Kustomize (base + overlays) for deploying all 8 microservices to any K8s cluster.

**Delivered:**

### Kustomize Structure (`infrastructure/kubernetes/`)
- **Base** (17 resource files): canonical resource definitions for all components
- **Staging overlay**: `ledgerlite-staging` namespace, `:staging` image tags, staging secrets
- **Production overlay**: `ledgerlite-production` namespace, `:production` image tags, 2 replicas per microservice

### Base Resources
- **Namespace** — `ledgerlite` (overridden per overlay)
- **ConfigMap** — `JWT_ALGORITHM=HS256`
- **Secret** — `JWT_SECRET`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_URL` (dev defaults, replaced per overlay)
- **PostgreSQL StatefulSet** — Postgres 16-alpine, 5Gi PVC, `pg_isready` liveness/readiness probes
- **Redis Deployment** — Redis 7-alpine with AOF persistence, `redis-cli ping` probes
- **Migrations Job** — runs `alembic upgrade head` using `database/Dockerfile` image
- **8 Service Deployments + Services** — one per microservice, each with:
  - Service-prefixed env vars (`AUTH_`, `USER_`, `TXN_`, `LEDGER_`, `REPORT_`, `AI_`, `NOTIFICATION_`, `SYNC_`)
  - Dedicated Redis DB (0-7)
  - `/health` liveness and readiness probes
  - Resource limits: 50m/200m CPU, 64Mi/256Mi memory
- **Ingress** — nginx-ingress with 12 path-based routing rules (regex rewrite)

### Ingress Routing

| Path | Backend |
|------|---------|
| `/api/auth/*` | auth-service:8000 |
| `/api/users/*` | user-service:8000 |
| `/api/transactions/*` | transaction-service:8000 |
| `/api/accounts/*` | transaction-service:8000 |
| `/api/categories/*` | transaction-service:8000 |
| `/api/customers/*` | ledger-service:8000 |
| `/api/ledger-entry/*` | ledger-service:8000 |
| `/api/ledger/*` | ledger-service:8000 |
| `/api/reports/*` | report-service:8000 |
| `/api/ai/*` | ai-service:8000 |
| `/api/notifications/*` | notification-service:8000 |
| `/api/sync/*` | sync-service:8000 |

### Overlay Differences

| Aspect | Staging | Production |
|--------|---------|------------|
| Namespace | `ledgerlite-staging` | `ledgerlite-production` |
| Replicas per service | 1 | 2 |
| Image tag | `:staging` | `:production` |
| Ingress host | `api.staging.ledgerlite.app` | `api.ledgerlite.app` |
| Secrets | Staging defaults | Placeholder (replace with sealed-secrets) |

### Also Delivered
- `database/Dockerfile` — lightweight Python 3.12 image for running Alembic migrations in K8s

**File Count:** 23 YAML files + 1 Dockerfile

**Validation:** `kubectl kustomize` renders correctly for both staging and production overlays (25 resources each: 1 NS + 1 CM + 1 Secret + 1 StatefulSet + 9 Deployments + 10 Services + 1 Ingress + 1 Job)

**Key Decisions:**
- Kustomize over Helm — built into kubectl, no extra tooling, simpler for straightforward overlays
- All services use internal port 8000 (uvicorn default) — no port mapping needed
- PostgreSQL StatefulSet included for dev/staging self-containment; production can swap to managed RDS/CloudSQL
- Migrations run as a standalone Job (manual apply before deployments), not auto-run on every `kubectl apply`
- Secrets use `stringData` (not base64) for readability; production should use sealed-secrets or external-secrets-operator

---

## Sprint 9 — Next.js Web Dashboard (Completed — `sprint-9-done`)

**Goal:** Scaffold and ship a Next.js 14 web dashboard with TypeScript, 6 functional tabs, and auth integration.

**Delivered:**
- Next.js 14 app in `apps/web-dashboard/` with App Router
- 6 tabs: Dashboard, Transactions, Accounts, Ledger, Reports, Settings
- Auth: JWT-based login flow integrated with auth-service
- Recharts for reports visualisation
- `lib/config.ts` + `.env.local.example` for service URL configuration
- TypeScript throughout; Tailwind CSS for UI

---

## Sprint 10 — GCP Staging Deploy (Completed — `sprint-10-done`)

**Goal:** Deploy all 8 microservices to a live GCP staging environment (GKE + Cloud SQL + Redis).

**Delivered:**
- GKE Standard cluster `ledgerlite-staging` in `us-central1` (3 preemptible e2-medium nodes)
- Cloud SQL Postgres 16 instance `ledgerlite-staging-pg` at private IP `10.82.0.3`
- Redis 7 in-cluster (Memorystore path deferred; in-cluster Redis for staging)
- All 8 services deployed in namespace `ledgerlite-staging` and verified Running
- Alembic migrations ran successfully — schema + seed categories applied
- GHCR image registry at `ghcr.io/sunnysanthosh/ledgerlite/<service>:latest`
- Terraform IaC for GCP (`infrastructure/terraform/`) — 6 modules: vpc, gke, cloudsql, memorystore, storage, iam

**Key decisions:**
- GKE Standard (not Autopilot) for cost predictability
- Preemptible nodes for staging cost savings (~$30/mo vs $90/mo)
- Private VPC — Cloud SQL accessible only within cluster

---

## Sprint 11 — Production Readiness: HA + TLS + CI Hardening (Completed — `sprint-11-done`)

**Goal:** Make staging production-grade — HTTPS, auto-scaling, verified deploys, security scanning on every build.

**Delivered:**
- `deploy.yml`: KUBECONFIG/DB_PASSWORD/JWT_SECRET env secrets; smoke tests; auto-rollback; removed `--record`
- `build.yml`: Trivy CRITICAL/HIGH scan after every image build
- `test.yml`: pytest-cov XML artifact (14-day retention)
- `lint.yml`: terraform-lint job (`fmt` + `validate`)
- `base/resource-quota.yaml`: pods:40, cpu:4, mem:4Gi
- `base/pdb.yaml`: PodDisruptionBudget minAvailable:1 for all 8 services
- `base/hpa.yaml`: autoscaling/v2 CPU-50%, min:1 max:4 (staging), min:2 max:6 (production)
- `base/kustomization.yaml`: commonLabels → labels (kustomize v5)
- `cert-manager/`: ClusterIssuer manifests for Let's Encrypt staging + production
- `overlays/staging`: TLS via letsencrypt-staging + ssl-redirect
- `overlays/production`: TLS via letsencrypt-prod, HPA min:2 max:6 patch
- `docs/operations/github-secrets-setup.md`: one-time setup guide

---

## Sprint 12 — Data Reliability + App Correctness + Cost Visibility (Completed — `sprint-12-done`)

**Goal:** GCP Budget Alerts live, staging auto-stops nightly, no Redis data loss on restart, correct DB query performance, app works end-to-end in staging, rate limiting active.

**Delivered:**
- **TD-33**: On-demand staging start/stop (nightly 22:00 UTC cron), CI SA in Terraform IAM
- **TD-15**: Migration 002 idempotent (WHERE NOT EXISTS replaces bulk_insert)
- **TD-16**: Migration 003 — 4 missing FK indexes (categories, transactions.category_id partial, customers, receipts)
- **TD-20**: Migration 001 downgrade() — drops all 10 tables in reverse order
- **TD-14**: CORSMiddleware on all 8 services (ALLOWED_ORIGINS env-overridable)
- **TD-19**: slowapi rate limiting 100 req/min per IP on all 8 services
- **TD-23**: logger.exception() in db/session.py except block on all 8 services
- **TD-17**: Redis StatefulSet + 1Gi PVC + headless Service (AOF + RDB persistence)
- **TD-11**: Flutter AppConfig + standardised env vars (AUTH_URL…SYNC_URL, --dart-define)
- **TD-12**: Next.js lib/config.ts + .env.local.example + sync service added
- **FT-02**: cost-snapshot.yml CI job — captures GKE/SQL state on sprint-*-done tag push
- **TD-32**: docs/operations/budget-alerts-setup.md — gcloud CLI + console steps

---

## Sprint 13 — Security Hardening + Observability + Admin Cost Dashboard + RBAC (Completed — `sprint-13-rbac-baseline`)

**Goal:** Admin cost dashboard live, zero implicit pod-to-pod access, full request tracing, hardened mobile client, documented RBAC model.

**Delivered:**
- **TD-28**: Slack CI failure alerts on test.yml + lint.yml + build.yml
- **FT-01**: Admin cost dashboard — Next.js `/infra` page with budget bars, trend chart, resource table
- **TD-22**: Docker base image digest pinning — all 9 Dockerfiles `FROM python:3.12-slim@sha256:...`
- **TD-10**: Kubernetes NetworkPolicies — 7 policies (default-deny + service-specific allow rules)
- **TD-21**: Structured JSON logging + X-Trace-ID middleware on all 8 services
- **TD-25**: 60% coverage gate — `--cov-fail-under=60` in test.yml; all services at 84–91%
- **TD-26**: Flutter cert pinning — ISRG Root X1 CA, opt-in via `--dart-define=CERT_PIN_ENABLED=true`
- **PR #14**: Admin RBAC — `adminOnly` sidebar flag + `isAdmin()` client helper + page redirect guard
- **PR #15**: Server-side auth on `/api/infra/costs` — `resolveAdminStatus()` fails closed; `ADMIN_EMAILS` server-only
- **PR #16**: git-ignored admin runbooks + `docs/admin/README.md` placeholder committed
- **PR #17**: RBAC docs — `docs/developer/rbac-guide.md`, `docs/product/user-personas.md`, Architecture §7, CLAUDE.md RBAC conventions

**Tests:** 146 tests across 8 services, all green. Coverage gate 60% min enforced in CI.

---

## Sprint 14 — Multi-User Organisations — Backend (Completed — `sprint-14-done`)

**Goal:** Introduce an organisation layer so multiple users can share a set of financial records (e.g., a business owner and their accountant). Unified model: every user — even solo users — gets a personal org automatically, keeping the query model consistent.

**Delivered:**

### Database (2 new Alembic migrations)

**Migration 004 — `004_organisations.py`**
- New tables: `organisations` (id, name, owner_id, is_personal, is_active) and `org_memberships` (id, org_id, user_id, role, is_active, invited_by)
- Role constraint: `CHECK (role IN ('owner','member','read_only'))`
- Unique constraint: `(org_id, user_id)` — one membership row per user per org
- Added nullable `org_id` column to six existing tables: `accounts`, `transactions`, `categories`, `customers`, `ledger_entries`, `notifications`
- Indexes on all `org_id` columns and membership lookups

**Migration 005 — `005_personal_orgs_data_migration.py`**
- Pure data migration: creates one personal org per existing user, inserts owner membership, backfills `org_id` on all six data tables using the user's personal org

### Auth Service
- New read-only `Organisation` + `OrgMembership` ORM models (`models/org.py`)
- Extended `UserProfile` schema with `organisations: list[OrgRef]`
- `GET /auth/me` now eager-loads memberships via `selectinload` and returns the user's org list

### User Service — Full Org CRUD (7 new endpoints)
- `get_org_member` FastAPI dependency in `services/security.py`: reads `X-Org-ID` header, verifies org membership, falls back to personal org when header absent; raises 403 if not a member
- `POST /organisations` — create new org (creator becomes owner)
- `GET /organisations` — list user's orgs (from `org_memberships`)
- `GET /organisations/{org_id}` — get org detail with member list
- `POST /organisations/{org_id}/members` — invite user by email (owner/member only)
- `GET /organisations/{org_id}/members` — list members
- `PATCH /organisations/{org_id}/members/{user_id}` — change role (owner only)
- `DELETE /organisations/{org_id}/members/{user_id}` — remove member (owner only; cannot remove last owner)

### Transaction, Ledger, Report Services — Org-Scoped Data
- Read-only `Organisation` + `OrgMembership` ORM models added to each service
- `org_id` column added to `Account`, `Transaction`, `Customer`, `LedgerEntry` models (nullable, no FK constraint for SQLite test compatibility)
- All queries converted from `user_id` scope → `org_id` scope
- All create operations write both `user_id` (audit) and `org_id` (scope)
- `get_org_member` dependency wired into all route handlers; `membership.org_id` passed to service functions

### Shared Test Data (`shared/test_data.py`)
- Deterministic org UUIDs: `ORG_PRIYA_ID`…`ORG_ARJUN_ID` (`00000000-0000-4000-0100-00000000000X`)
- `USER_ORG_MAP` dict: maps each test user's ID to their personal org ID
- `make_auth_headers()` extended with optional `org_id` parameter → adds `X-Org-ID` header
- All per-user header factories (`priya_headers()`, `rajesh_headers()`, etc.) now include `X-Org-ID`

### Test Fixtures Updated (transaction, ledger, report services)
- `seed_user` creates personal org + owner membership; attaches `user._org_id` transient attr
- `auth_headers` includes `{"Authorization": "Bearer …", "X-Org-ID": "…"}`
- `seed_account` / `seed_customer` set `org_id` from `seed_user._org_id`
- `seed_full_data` (report-service) creates orgs + memberships for all 6 test users, seeds `org_id` on all data rows

**Endpoints added:**

| Service | Method | Path | Status | Description |
|---------|--------|------|--------|-------------|
| user-service | POST | /organisations | 201 | Create org |
| user-service | GET | /organisations | 200 | List user's orgs |
| user-service | GET | /organisations/{org_id} | 200 | Get org detail |
| user-service | POST | /organisations/{org_id}/members | 201 | Invite member by email |
| user-service | GET | /organisations/{org_id}/members | 200 | List members |
| user-service | PATCH | /organisations/{org_id}/members/{uid} | 200 | Change member role |
| user-service | DELETE | /organisations/{org_id}/members/{uid} | 204 | Remove member |
| auth-service | GET | /auth/me | 200 | Now returns `organisations` list |

**Tests:** 158 passing across all 8 services (30 user-service, 27 transaction, 26 ledger, 18 report, 15 auth, 16 ai, 14 sync, 12 notification)

**Key Technical Decisions:**
- **Unified model:** every user automatically gets a personal org — solo users are unaffected; no migration path needed for existing data
- **`X-Org-ID` header transport:** clients specify the active org context; absent header falls back to personal org transparently
- **`user_id` preserved on all tables** for audit; `org_id` is the query scope — both columns exist side-by-side
- **`org_id` nullable with no FK constraint in ORM:** uses plain `Uuid` (cross-dialect) not `postgresql.UUID` — FK constraints are enforced at DB level only, keeping SQLite test backend working without FK enforcement
- **`populate_existing=True`** on all `get_org_member` queries to bust the SQLAlchemy identity map cache after membership lookups
- **`user._org_id` transient attribute pattern:** attaches Python-level attribute (not a DB column) to the `seed_user` fixture return value so `auth_headers` can read the org ID without an extra DB query

**Deferred to Sprint 15:**
- Web dashboard: `OrgRef` types, Zustand `currentOrgId` store, `OrgSwitcher` component, `X-Org-ID` in API client, `/settings/org` page
- Flutter mobile: `AuthState.organisations`, `TokenStorage.getCurrentOrgId()`, `AuthInterceptor` header injection, `/org-selection` route + screen
- Org scoping for ai-service, notification-service, sync-service
- `org_id NOT NULL` constraint (after all services verified in production)

---

## Sprint 15 — Org UI Layer + Remaining Service Org Scoping (Completed — `sprint-15-done`)

**Goal:** Complete the org feature end-to-end: wire `X-Org-ID` into web dashboard, Flutter mobile, and scope the three remaining backend services (ai, notification, sync) to org_id.

**Delivered:**

### Web Dashboard
- `types/api.ts`: `OrgRef`, `OrgMemberResponse`, `OrgResponse`, `OrgMemberInvite`, `OrgMemberPatch` interfaces; `UserProfile.organisations?: OrgRef[]`
- `lib/store/auth-store.ts`: `currentOrgId` + `organisations` in Zustand state; `setCurrentOrg` + `setOrganisations` actions; both persisted in `ledgerlite-auth` localStorage key
- `components/layout/org-switcher.tsx` (NEW): dropdown visible only when `organisations.length > 1`; on select calls `setCurrentOrg` + invalidates all React Query caches
- `components/layout/sidebar.tsx`: renders `<OrgSwitcher />` above nav
- `lib/api/client.ts`: injects `X-Org-ID` header on every request from persisted store
- `lib/api/orgs.ts` (NEW): `getOrg`, `listOrgMembers`, `inviteMember`, `updateMemberRole`, `removeMember` API wrappers
- `app/(dashboard)/settings/org/page.tsx` (NEW): org management UI — member list with role dropdown + remove, invite-by-email form (hidden for personal orgs)
- `app/(dashboard)/layout.tsx`: hydrates `organisations` from `/auth/me` if store is empty

### Flutter Mobile
- `auth_provider.dart`: `AuthState.organisations` + `currentOrgId`; `login()`/`register()` parse orgs; `switchOrganisation(id)` method; `logout()` clears org
- `token_storage.dart`: `saveCurrentOrgId` / `getCurrentOrgId` / `clearOrgId` (flutter_secure_storage)
- `auth_interceptor.dart`: injects `X-Org-ID` from `_tokenStorage.getCurrentOrgId()` in `onRequest`
- `app_router.dart`: `/org-selection` route; redirect to `/org-selection` if `organisations.length > 1` and `currentOrgId == null`
- `features/orgs/screens/org_selection_screen.dart` (NEW): tap-to-select list with role badges; `switchOrganisation(id)` → `/dashboard`

### Backend — ai-service
- `models/org.py` (NEW): read-only `Organisation` + `OrgMembership` ORM
- `models/transaction.py` + `models/category.py`: added `org_id` column
- `services/security.py`: added `get_org_member` dependency (same pattern as report-service)
- `services/ai_service.py`: `categorize_transaction` + `get_spending_insights` now scoped to `org_id`; system categories matched by `org_id IS NULL`
- `routers/ai.py`: `categorize` + `insights` use `get_org_member`; `ocr` keeps `get_current_user`
- `tests/conftest.py`: seeds org + membership; `auth_headers` includes `X-Org-ID`; `seed_transactions` sets `org_id`

### Backend — notification-service
- `models/org.py` (NEW): read-only ORM
- `models/notification.py` + `models/customer.py` + `models/ledger_entry.py`: added `org_id`
- `services/security.py`: added `get_org_member`
- `services/notification_service.py`: `list_notifications` scoped to `org_id`; `create_reminder` uses `org_id` for customer + ledger_entry lookup; notification created with `org_id`
- `routers/notifications.py`: `list` + `send_reminder` use `get_org_member`; `mark_read` keeps `get_current_user` (ownership stays user-scoped)
- `tests/conftest.py`: seeds orgs + memberships for all shared users; `org_id` on customers, ledger_entries, notifications

### Backend — sync-service
- `models/org.py` (NEW): read-only ORM
- `models/transaction.py` + `models/ledger_entry.py`: added `org_id`
- `services/security.py`: added `get_org_member`
- `services/sync_service.py`: `push_changes` upserts/creates by `org_id`; `pull_changes` fetches by `org_id`; `get_sync_status` counts pending changes by `org_id`; `SyncLog` stays user+device scoped
- `routers/sync.py`: all 3 endpoints use `get_org_member`; pass `membership.user_id` + `membership.org_id`
- `tests/conftest.py`: seeds org + membership; `auth_headers` includes `X-Org-ID`; `seed_server_transactions` sets `org_id`

**Tests:** 158 passing (16 ai + 12 notification + 14 sync + unchanged 116 from other services). Lint clean.

**Key decisions:**
- SyncLog stays `user_id`-scoped (per-device per-user tracking, not org-level)
- Notification `mark_as_read` stays `user_id`-scoped (ownership of a notification is per-user)
- System categories (`org_id IS NULL`) still match for all orgs — same pattern as `user_id IS NULL` before

**Deferred to Sprint 16:**
- `org_id NOT NULL` constraints (after all services verified in production)
- Org invitation email notifications
- Audit log for org actions
