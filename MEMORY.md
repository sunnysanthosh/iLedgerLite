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

### Week of 2026-06-15 — session wrap-up (resume point)

- **Sprint 17 closed and tagged:** `sprint-17-done` at `97a64a5` (PR #26 merged, squash). Covered
  granular org permissions (PERMISSION_PRESETS, migration 008, `require_scope`, accountant/staff
  roles) and transactional email delivery (welcome + invite emails).
- **SaaSpocalypse assessment done:** `docs/SaaSpocalypse-Assessment.md` — LLM-as-Judge review of
  whether iLedgerLite needs rearchitecting for the agent era. Verdict: current direction is sound,
  nourish it; near-term adds are `actor_type` on audit_log, tool/contract layer, real LLM in
  ai-service, agent-approval spike. TD-34 (LLM provider abstraction) added to ROADMAP Tier 2,
  targeted for S18.
- **Billing incident resolved:** GCP billing account `01A637-1B4A4F-58C83D` on project
  `project-6737f3c2-e011-49b7-ae4` was found `OPEN: False` (caused 403s on all `gcloud container`
  calls). User re-enabled billing; verified `billingEnabled: true`. Documented in
  `docs/operations/cost-snapshots.md`.
- **Cloud SQL start/test/stop cycle done:** started `ledgerlite-staging-pg`, ran full local 4-gate
  suite (180 unit + 13 smoke + 26 regression — all green), confirmed live staging pods are
  `Pending` (separate, pre-existing capacity issue — GKE has 1 node vs ~3 needed for all 9 pods;
  not fixed, just documented).
- **GKE cost reduction:** scaled `ledgerlite-staging` node pool to 0 (verified via
  `gcloud compute instance-groups list`, not the stale `NUM_NODES` field). **Current infra state:
  GKE = 0 nodes, Cloud SQL = STOPPED. Staging is fully hibernated.** Start only for a true E2E
  run, then stop immediately — see `docs/operations/environment-lifecycle.md`.
- **New team policy codified:** "Where Do Tests Run?" in `docs/operations/environment-lifecycle.md`
  — all unit tests and the 4-gate suite run locally (`.venv`, no cloud); Docker Compose for manual
  API exploration; staging started only for true E2E verification of the deployed env. Also added
  a "gcloud Quirks & Gotchas" table (billing-disabled 403, stale `NUM_NODES`, Cloud SQL
  patch hang/409) to the same doc.
- **Next session starts with:** Sprint 18 planning (see candidate scope below) — staging is
  hibernated, no cleanup needed; just `make dev-start` + `.venv` for local work.

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
