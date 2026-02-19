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
