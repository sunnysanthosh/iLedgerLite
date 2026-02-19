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
