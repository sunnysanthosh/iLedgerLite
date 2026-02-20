# LedgerLite — Implementation Roadmap

## Current State (as of Sprint 6B)

| Component | Status |
|-----------|--------|
| **auth-service** | Done — 4 endpoints, 15 tests |
| **user-service** | Done — 5 endpoints, 18 tests |
| **transaction-service** | Done — 12 endpoints, 27 tests |
| **ledger-service** | Done — 7 endpoints, 26 tests |
| **report-service** | Done — 5 endpoints, 18 tests |
| **notification-service** | Done — 3 endpoints, 12 tests |
| **ai-service** | Done — 3 endpoints, 16 tests |
| **sync-service** | Done — 3 endpoints, 14 tests |
| **database/schema.sql** | Done — 10 tables, indexes |
| **database/seeds/** | Done — 29 system categories |
| **database/migrations/** | Done — Alembic (initial schema + seed migration) |
| **docker-compose.yml** | Done — prefixed env vars, JWT_SECRET, correct Redis DBs |
| **CI/CD** | Done — test, lint, build (GHCR), deploy (staging/prod) |
| **docs/** | Done — API.md, SPRINT-LOG.md |
| **shared/** | Done — base settings, pagination, auth utilities |
| **CLAUDE.md** | Done — coding conventions, testing patterns, CI/CD, branching strategy |
| **apps/mobile-app** | Done — Flutter (auth, dashboard, transactions, accounts, ledger, reports, settings, offline sync) — 43 Dart files |
| **apps/web-dashboard** | Done — Next.js 14, 6 tabs (dashboard, transactions, accounts, ledger, reports, analytics), TypeScript, Recharts, TanStack Query, Zustand |
| **infrastructure/kubernetes** | Done — Kustomize base + staging/production overlays (23 manifests) |
| **infrastructure/terraform** | Empty (.gitkeep) — deferred to 6C |

**Total: 146 tests passing across 8 services**
**All backend microservices complete. Flutter mobile app feature-complete (Sprint 8). Web dashboard complete (Sprint 9).**

---

## Sprint 1 — User Service + Shared Foundations (DONE)

> **Goal:** User profiles, settings, onboarding — and extract shared patterns from auth-service.

### 1A. Shared Module (`shared/`)
- [ ] `shared/configs/base_settings.py` — common Settings base (DB URL, Redis URL)
- [ ] `shared/models/base.py` — shared `DeclarativeBase`
- [ ] `shared/utils/pagination.py` — `PaginationParams` dependency, paginated response helper
- [ ] `shared/utils/auth.py` — `get_current_user` dependency (decode JWT, usable by any service)

### 1B. User Service (`services/user-service`)
- [ ] `config.py` — service settings
- [ ] `db/session.py` — async engine + `get_db`
- [ ] `models/user.py` — User ORM model (reuse from auth or import shared)
- [ ] `schemas/user.py` — `UserProfile`, `UserUpdate`, `OnboardingRequest`, `SettingsUpdate`
- [ ] `services/user_service.py` — get profile, update profile, onboarding, deactivate
- [ ] `routers/user.py` — endpoints:
  - `POST /users/onboarding` — account_type, currency, language, business_category
  - `GET /users/{id}/profile` — full profile
  - `PUT /users/{id}/profile` — update name, phone, email
  - `PUT /users/{id}/settings` — notifications, language, currency
  - `DELETE /users/{id}` — soft-deactivate
- [ ] `tests/` — 10+ test cases (CRUD, auth-required, validation)

**Depends on:** auth-service (JWT tokens for protected endpoints)

---

## Sprint 2 — Transaction Service (DONE)

> **Goal:** Transaction CRUD with category tagging — the heart of the product.

### 2A. Transaction Service (`services/transaction-service`)
- [ ] `models/` — `Transaction`, `Account`, `Category` ORM models
- [ ] `schemas/transaction.py` — `TransactionCreate`, `TransactionUpdate`, `TransactionResponse`, `TransactionList`
- [ ] `schemas/account.py` — `AccountCreate`, `AccountResponse`
- [ ] `schemas/category.py` — `CategoryCreate`, `CategoryResponse`
- [ ] `services/transaction_service.py` — create, list (with filters), update, delete, balance recalculation
- [ ] `services/account_service.py` — account CRUD, balance tracking
- [ ] `services/category_service.py` — system + user categories, list by type
- [ ] `routers/transactions.py` — endpoints:
  - `POST /transactions` — create (account_id, amount, category_id, type, payment_method, notes)
  - `GET /transactions` — list with filters (account_id, date_range, category_id, type) + pagination
  - `GET /transactions/{id}` — single transaction detail
  - `PUT /transactions/{id}` — update
  - `DELETE /transactions/{id}` — soft delete
- [ ] `routers/accounts.py` — endpoints:
  - `POST /accounts` — create (name, type, currency)
  - `GET /accounts` — list user's accounts
  - `GET /accounts/{id}` — detail with balance
  - `PUT /accounts/{id}` — update name/type
  - `DELETE /accounts/{id}` — deactivate
- [ ] `routers/categories.py` — endpoints:
  - `POST /categories` — create custom category
  - `GET /categories` — list (system + user, filter by income/expense)
- [ ] `tests/` — 20+ test cases (CRUD, filters, balance math, auth, validation)

### 2B. Database Seed — System Categories
- [ ] `database/seeds/categories.sql` — default income/expense categories (Salary, Rent, Food, Transport, Utilities, Shopping, etc.)

---

## Sprint 3 — Ledger Service (DONE)

> **Goal:** Customer credit tracking for shop owners — the differentiating feature.

### 3A. Ledger Service (`services/ledger-service`)
- [ ] `models/` — `Customer`, `LedgerEntry` ORM models
- [ ] `schemas/customer.py` — `CustomerCreate`, `CustomerUpdate`, `CustomerResponse`, `CustomerList`
- [ ] `schemas/ledger.py` — `LedgerEntryCreate`, `LedgerEntryResponse`, `LedgerSummary`
- [ ] `services/customer_service.py` — customer CRUD, outstanding balance calculation
- [ ] `services/ledger_service.py` — create entry, settle, partial payment, history
- [ ] `routers/customers.py` — endpoints:
  - `POST /customers` — create (name, phone, email, address)
  - `GET /customers` — list with outstanding balance indicator + search
  - `GET /customers/{id}` — detail with credit summary
  - `PUT /customers/{id}` — update info
- [ ] `routers/ledger.py` — endpoints:
  - `POST /ledger-entry` — create (customer_id, amount, type=debit/credit, due_date, description)
  - `GET /ledger/{customer_id}` — full credit history + outstanding balance
  - `PUT /ledger-entry/{id}` — mark settled / partial payment
- [ ] `tests/` — 15+ test cases (CRUD, balance calc, settlement, overdue filtering)

---

## Sprint 4 — Report Service + Notification Service (DONE)

> **Goal:** Financial reports and payment reminders.

### 4A. Report Service (`services/report-service`)
- [ ] `services/report_service.py` — aggregate calculations (calls transaction & ledger DBs or their APIs)
- [ ] `routers/reports.py` — endpoints:
  - `GET /reports/profit-loss` — revenue, expenses, profit by date range
  - `GET /reports/cashflow` — inflows, outflows, net by period
  - `GET /reports/budget` — budget vs actual by category
  - `GET /reports/summary` — dashboard aggregation (totals, top categories)
  - `GET /reports/export` — PDF/Excel generation (format query param)
- [ ] `tests/` — 10+ test cases

### 4B. Notification Service (`services/notification-service`)
- [ ] `models/notification.py` — Notification model (user_id, type, message, is_read, sent_at)
- [ ] `services/notification_service.py` — create notification, mark read, send via channel
- [ ] `services/channels/` — email (SMTP), SMS (Twilio/MSG91 stub), push (FCM stub)
- [ ] `routers/notifications.py` — endpoints:
  - `GET /notifications` — list user's notifications
  - `PUT /notifications/{id}/read` — mark as read
  - `POST /notifications/reminder` — trigger credit reminder for a customer
- [ ] `tests/` — 8+ test cases

---

## Sprint 5 — Sync Service + AI Service (Offline-First & Intelligence)

> **Goal:** Offline SQLite sync and AI-powered categorization.

### 5A. Sync Service (`services/sync-service`)
- [ ] `models/sync.py` — SyncLog model (device_id, last_synced, sync_status)
- [ ] `services/sync_service.py` — conflict resolution (last-write-wins or merge), delta calculation
- [ ] `routers/sync.py` — endpoints:
  - `POST /sync/push` — upload local changes (batch of transactions/ledger entries)
  - `GET /sync/pull` — download server changes since last sync timestamp
  - `GET /sync/status` — last sync time, pending count
- [ ] `tests/` — 10+ test cases (conflict scenarios, delta sync, idempotency)

### 5B. AI Service (`services/ai-service`)
- [ ] `services/categorization.py` — rule-based + keyword-matching categorizer (MVP, no ML yet)
- [ ] `services/insights.py` — spending anomaly detection (simple statistical: >2σ from rolling mean)
- [ ] `routers/ai.py` — endpoints:
  - `POST /ai/categorize` — predict category from description/amount
  - `GET /ai/insights` — spending anomalies, trends for a user
  - `POST /ai/ocr` — receipt image → extracted fields (stub, returns mock)
- [ ] `tests/` — 8+ test cases

---

## Sprint 6 — Database Migrations + Infrastructure

> **Goal:** Production-grade database management and deployment config.

### 6A. Alembic Migrations (`database/migrations/`) — DONE
- [x] Initialize Alembic config (unified at `database/` with env var override)
- [x] Generate initial migration from `schema.sql` (10 tables, all indexes, check constraints)
- [x] Add seed data migration (29 system categories — 8 income + 21 expense)

### 6B. Kubernetes Manifests (`infrastructure/kubernetes/`) — DONE
- [x] Kustomize base + overlays (staging/production)
- [x] Deployment + Service YAML per microservice (8 services)
- [x] ConfigMap for JWT_ALGORITHM
- [x] Secret for JWT_SECRET, DB credentials, DATABASE_URL
- [x] nginx-ingress with 12 path-based routing rules
- [x] PostgreSQL 16 StatefulSet with 5Gi PVC and health probes
- [x] Redis 7 Deployment with AOF persistence and health probes
- [x] Alembic migrations Job + Dockerfile (`database/Dockerfile`)
- [x] Staging overlay: ledgerlite-staging namespace, staging image tags, staging secrets
- [x] Production overlay: ledgerlite-production namespace, 2 replicas per service, production image tags

### 6C. Terraform (`infrastructure/terraform/`) — DEFERRED
- [ ] VPC, subnets, security groups
- [ ] EKS/GKE cluster module
- [ ] RDS/CloudSQL for PostgreSQL
- [ ] ElastiCache/Memorystore for Redis
- [ ] S3/GCS bucket for receipt uploads
- [ ] IAM roles and policies

### 6D. CI/CD (`.github/workflows/`) — DONE
- [x] `test.yml` — run pytest per service on PR (done in Retro 4.5)
- [x] `lint.yml` — ruff check + format check (done in Retro 4.5)
- [x] `build.yml` — Docker build + push to GHCR (per-service, change detection)
- [x] `deploy.yml` — manual deploy to staging/production via kubectl

---

## Sprint 7 — Flutter Mobile App (MVP Screens)

> **Goal:** Core mobile experience — login, dashboard, transaction entry.

### 7A. Flutter Project Setup (`apps/mobile-app/`) — DONE
- [x] Clean Architecture folder structure (core/, features/, assets/)
- [x] State management: Riverpod (flutter_riverpod + riverpod_annotation)
- [x] SQLite local database: sqflite dependency ready
- [x] API client layer: Dio + AuthInterceptor for JWT auto-attach + refresh
- [x] Theme system: Material 3, light/dark, LedgerLite brand colors

### 7B. Auth Flow — DONE
- [x] Login screen (email + password, form validation, error display)
- [x] Registration screen (name, email, phone, password with confirmation)
- [x] Secure token storage (flutter_secure_storage with encrypted prefs)
- [x] Auto-refresh token interceptor (401 → refresh → retry)

### 7C. Dashboard Screen — DONE
- [x] Total balance card with income/expense summary
- [x] Quick stats row (account count, transaction count)
- [x] Recent transactions list (last 5)
- [x] Quick-add floating action button

### 7D. Transaction Screens — DONE
- [x] Transaction list with type filter (income/expense/transfer)
- [x] Add transaction form (amount, account picker, category picker, date, description)
- [x] Category dropdown filtered by transaction type

### 7E. Account Management — DONE
- [x] Account list screen with balance display and type icons
- [x] Add account form (name, type chips, currency selector)

---

## Sprint 8 — Mobile Ledger + Reports + Offline Sync (DONE)

> **Goal:** Business ledger on mobile, report viewing, and offline capability.

### 8A. Business Ledger Screens — DONE
- [x] Customer list with search + outstanding balance
- [x] Customer detail with credit history timeline
- [x] Add ledger entry form (debit/credit with due date)
- [x] Mark payment — full settle and partial payment (settle dialog with amount input + validation)
- [x] Add customer form (name, phone, email, address)

### 8B. Reports Screens — DONE
- [x] Monthly spending breakdown (fl_chart PieChart with color legend)
- [x] P&L view with Personal/Business mode toggle (revenue/income, expenses, net profit)
- [x] Date range picker bar (custom range or all-time)
- [x] Export with format picker (CSV or PDF)
- [x] Category list with transaction counts

### 8C. Offline Sync — DONE
- [x] Local SQLite mirror of transactions/ledger (sqflite)
- [x] Background sync worker (push/pull cycle, periodic timer)
- [x] Sync status indicator in settings UI
- [x] Last-write-wins conflict resolution

### 8D. Settings Screen — DONE
- [x] Profile section with avatar initials, name, email, phone
- [x] Profile edit bottom sheet (full name, phone, business name) with save
- [x] Sync status with manual sync trigger
- [x] Currency picker (INR, USD, EUR, GBP) — reads current from profile
- [x] Language picker (English, Hindi, Tamil, Telugu) — reads current from profile
- [x] Notification preferences (push + email toggles) — reads live values from profile
- [x] Logout with confirmation dialog
- [x] Updated bottom nav to 5 tabs (Home, Transactions, Ledger, Reports, Settings)

---

## Post-MVP Phases (Month 5+)

### Phase 2 — Growth Features
- [ ] OTP/phone-based login (replace email login for India market)
- [ ] Bank SMS parsing for auto-transaction import
- [ ] UPI payment integration
- [ ] Voice transaction entry
- [ ] Multi-language support (Hindi, Tamil, Telugu, etc.)
- [ ] Family view / shared household ledger
- [ ] Budget planner with alerts
- [ ] Receipt OCR (real implementation via Google Vision / Tesseract)
- [ ] AI expense categorization (ML model, not just keywords)
- [ ] Cashflow forecasting (time-series model)

### Phase 3 — Scale & Web
- [ ] Web dashboard (React + Next.js) — analytics, reports, team management
- [ ] Multi-user roles & permissions (RBAC)
- [ ] Accountant access portal
- [ ] GST-ready tax reports
- [ ] Advanced analytics dashboard
- [ ] iOS app release

### Phase 4 — Embedded Finance (Year 2)
- [ ] Payment processing integration
- [ ] Credit line offerings for businesses
- [ ] BNPL for small businesses
- [ ] Insurance recommendations
- [ ] Supplier payment management

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **Sprint 1-2** | Must-have for any usable product (auth + transactions) |
| **Sprint 3-4** | Business differentiator (ledger + reports + notifications) |
| **Sprint 5** | Technical excellence (offline sync + AI) |
| **Sprint 6** | Production readiness (infra + CI/CD) |
| **Sprint 7-8** | User-facing product (mobile app) |
| **Post-MVP** | Growth, scale, monetization |

---

## Architecture Diagram (Service Dependencies)

```
┌─────────────┐
│  Mobile App  │──────┐
│  (Flutter)   │      │
└─────────────┘      │
                      ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ Auth Service │◄─│ API Gateway  │─►│ User Service │
│    :8001     │  │  (future)    │  │    :8002     │
└─────────────┘  └──────┬───────┘  └──────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Transaction  │ │   Ledger     │ │   Report     │
│   Service    │ │   Service    │ │   Service    │
│    :8003     │ │    :8004     │ │    :8005     │
└──────────────┘ └──────────────┘ └──────┬───────┘
                                         │ reads from
                                    ┌────┴────┐
                                    ▼         ▼
                              Transaction   Ledger
                                 DB          DB
        ┌───────────────────────────────────┐
        ▼               ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  AI Service  │ │ Notification │ │ Sync Service │
│    :8006     │ │   Service    │ │    :8008     │
└──────────────┘ │    :8007     │ └──────────────┘
                 └──────────────┘

┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │    Redis     │
│    :5432     │  │    :6379     │
└──────────────┘  └──────────────┘
```

---

## Recommended Next Step

**Sprint 9 is complete.** Next options: Sprint 6C (Terraform IaC) for cloud provisioning, or Post-MVP Phase 2 features (OTP login, bank SMS parsing, UPI integration, multi-language).
