# MEMORY.md

This file captures key project state for resuming work across sessions.

## Project State

- **Total tests:** 180 passing (15 auth + 34 user + 32 transaction + 30 ledger + 18 report + 21 notification + 16 ai + 14 sync) + 13 smoke + 26 regression
- **Completed sprints:** 0–17 (auth, user, transaction, ledger, report/notification, sync/ai, migrations, K8s, Terraform, Flutter, Next.js, GCP staging, HA/TLS, data reliability, security/RBAC, multi-user orgs backend+UI, org hardening, granular permissions + email delivery)
- **Next sprint:** 18 (TBD — see `docs/SPRINT-LOG.md` Sprint 17 "Deferred to Sprint 18" and `docs/SaaSpocalypse-Assessment.md`)
- **Services with full implementations:** all 8 (auth, user, transaction, ledger, report, ai, notification, sync)
- **ai-service caveat:** despite the name, categorization/insights/OCR are rule-based (keyword match, mocked OCR) — no real LLM yet. TD-34 tracks adding a provider-agnostic `LLMProvider` abstraction with GCP Vertex AI as the first implementation.

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

### Sprint 18 — candidate scope (not yet started)

Deferred from Sprint 17 (see `docs/SPRINT-LOG.md`):
- Org deletion / transfer ownership flows
- TD-34: provider-agnostic `LLMProvider` abstraction for `ai-service`, GCP Vertex AI as first
  concrete implementation (categorization/insights/OCR currently rule-based — no LLM at all)
- Agent-native foundations from `docs/SaaSpocalypse-Assessment.md`:
  - `actor_type` (human|agent) on `audit_log`
  - tool/contract layer over existing service APIs (scoped via Sprint 17's `require_scope`)
  - "agent proposes, human approves" spike flow
  - pull "Public API + API keys" and "Webhooks" forward from Phase 3 into Phase 2

**Shared infrastructure already in place:**
- `shared/configs/base_settings.py` — common Settings base (DB URL, Redis URL)
- `shared/utils/pagination.py` — PaginationParams dependency, paginated response helper
- `shared/utils/auth.py` — `get_current_user` dependency (decode JWT, usable by any service)
- `services/<name>-service/services/security.py` — `get_org_member`, `get_write_member`,
  `require_scope(scope)` dependencies for org-scoped + permission-scoped access

**Testing pattern:** Each service has its own `tests/` directory with `conftest.py` providing async test fixtures (test DB, test client, auth headers). Use `pytest tests/` from the service directory. Four-gate CI: `make test-schema && make test-all && make test-smoke && make test-regression` (or `make test-e2e`).

**Database:** PostgreSQL 16 with schema in `database/schema.sql`, 8 Alembic migrations. Tables: users, accounts, transactions, categories, customers, ledger_entries, receipts, user_settings, organisations, org_memberships (with `permissions` JSON), audit_log.
