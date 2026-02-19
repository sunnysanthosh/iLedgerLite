# MEMORY.md

This file captures key project state for resuming work across sessions.

## Project State

- **Total tests:** 86 passing (15 auth + 18 user + 27 transaction + 26 ledger)
- **Completed sprints:** 0 (auth), 1 (user + shared), 2 (transaction), 3 (ledger)
- **Next sprint:** 4 (report-service + notification-service)
- **Services with full implementations:** auth-service, user-service, transaction-service, ledger-service
- **Services still skeleton:** report-service, ai-service, notification-service, sync-service

## Critical Patterns

- **Async SQLAlchemy sessions:** Use `populate_existing=True` when merging model instances to avoid stale identity map cache
- **Monetary amounts:** Always use `Numeric(15, 2)` — never float
- **System categories:** `is_system=True, user_id=NULL` — visible to all users
- **Transaction deletion:** Hard delete (not soft) since balance reversal must be atomic
- **Ledger entries:** Hard records (not soft-deleted) since balance integrity depends on full history
- **SQLAlchemy `case()`:** Must be imported directly from sqlalchemy, NOT used as `func.case()` — `func.case()` is not valid in SQLAlchemy 2.x
- **Customer search:** Uses `ilike` for case-insensitive matching across name/phone/email
- **Outstanding balance:** sum(unsettled debits) - sum(unsettled credits); settled entries excluded
- **Token rotation:** Refresh tokens are single-use; used tokens are blacklisted in Redis
- **Anti-enumeration:** Auth returns identical errors for wrong password and nonexistent email

## Service Ports

| Service       | Port |
|---------------|------|
| auth          | 8001 |
| user          | 8002 |
| transaction   | 8003 |
| ledger        | 8004 |
| report        | 8005 |
| ai            | 8006 |
| notification  | 8007 |
| sync          | 8008 |

## Resume Context

### Sprint 4 — Report Service + Notification Service

**Report Service (port 8005):**
- Endpoints: profit-loss, cashflow, budget, summary, export (PDF/Excel)
- Reads from transaction and ledger databases (or their APIs)
- Aggregate calculations for financial reporting

**Notification Service (port 8007):**
- Endpoints: list notifications, mark as read, trigger credit reminder
- Channels: email (SMTP), SMS (stub), push (FCM stub)
- Notification model: user_id, type, message, is_read, sent_at

**Shared infrastructure already in place:**
- `shared/configs/base_settings.py` — common Settings base (DB URL, Redis URL)
- `shared/utils/pagination.py` — PaginationParams dependency, paginated response helper
- `shared/utils/auth.py` — `get_current_user` dependency (decode JWT, usable by any service)

**Testing pattern:** Each service has its own `tests/` directory with `conftest.py` providing async test fixtures (test DB, test client, auth headers). Use `pytest tests/` from the service directory.

**Database:** PostgreSQL 16 with schema in `database/schema.sql`. Tables: users, accounts, transactions, categories, customers, ledger_entries, receipts, user_settings.
