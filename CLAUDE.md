# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

LedgerLite is an **early-stage fintech SaaS product**. Backend microservices are under active development. Planning documents (PRDs, investor briefs, architecture blueprints) are at the root level. See `ROADMAP.md` for implementation status.

**Completed:** auth-service, user-service, transaction-service, ledger-service, report-service, notification-service, ai-service, sync-service, Alembic migrations (7 migrations), CI/CD (test + lint + build + deploy + coverage gate), Flutter mobile app (auth, dashboard, transactions, accounts, ledger, reports, settings, offline sync, org selection — 44+ Dart files), Kubernetes manifests (Kustomize base + staging/production overlays — 23 files), Next.js web dashboard (6 tabs + admin infra tab + org settings), Terraform IaC for GCP (6 modules — vpc, gke, cloudsql, memorystore, storage, iam), GCP staging live (all 8 services), multi-user organisations (full stack: Sprint 14 backend + Sprint 15 UI — OrgSwitcher, X-Org-ID header, OrgSelectionScreen, org scoping for all 8 services), org hardening (Sprint 16 — NOT NULL constraints, read_only enforcement, audit log, invite notifications — 171 tests)
**In Progress:** Sprint 17 planning
**Not Started:** Sprint 17 — granular org permissions, email delivery (SMTP/SendGrid), org deletion/transfer

## Python Environment

**Always use the project virtual environment. Never install packages globally.**

```bash
# First-time setup (project root)
python -m venv .venv                        # Python version pinned via .python-version (3.12.7)
source .venv/bin/activate                   # activate (Mac/Linux)
# .venv is git-ignored; .python-version is committed

# Install deps for a specific service into the active venv
pip install -r services/<name>-service/requirements.txt

# Or install all service deps at once (for IDE support / running all tests locally)
for req in services/*/requirements.txt; do pip install -r "$req"; done

# Deactivate when done
deactivate
```

**Rules:**
- `.venv/` is in `.gitignore` — never commit it.
- `.python-version` is committed — pyenv uses it to select Python 3.12.7 automatically.
- CI uses per-service fresh venvs (no shared state between service test runs).
- `pip install` outside an activated venv is forbidden.

## Build & Run Commands

```bash
# Start all services + Postgres + Redis (Docker — no venv needed)
docker compose up --build

# Start a single service for development (requires activated venv)
source .venv/bin/activate
cd services/<name>-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run tests for a single service (requires activated venv)
source .venv/bin/activate
cd services/<name>-service
python -m pytest tests/ -v

# Run all backend tests
for dir in services/*-service; do (cd "$dir" && python -m pytest tests/ -v); done

# Apply database schema (requires running Postgres)
psql -h localhost -U ledgerlite -d ledgerlite -f database/schema.sql

# Run Alembic migrations (from database/ directory)
cd database && alembic upgrade head

# Run migrations with custom DB URL
ALEMBIC_DATABASE_URL=postgresql://user:pass@host:5432/db alembic upgrade head
```

Service ports (via Docker Compose): auth=8001, user=8002, transaction=8003, ledger=8004, report=8005, ai=8006, notification=8007, sync=8008.

## Architecture

**Product:** Mobile-first accounting/ledger app for households and small businesses (India/SEA market).

**Tech stack:**
- **Mobile:** Flutter (Dart), Clean Architecture, Bloc/Riverpod, SQLite offline
- **Web:** React + Next.js
- **Backend:** Python 3.12 + FastAPI (8 microservices)
- **Database:** PostgreSQL 16 (primary), Redis 7 (cache)
- **Infra:** Docker Compose (dev), Kubernetes + Terraform (prod)

**Monorepo layout:**
```
apps/mobile-app/              # Flutter mobile app (43 Dart files)
apps/web-dashboard/           # Next.js (not yet scaffolded)
services/<name>-service/      # FastAPI microservices
  routers/                    # API route handlers
  models/                     # SQLAlchemy ORM models
  schemas/                    # Pydantic request/response schemas
  services/                   # Business logic + security
  db/                         # Database session
  tests/                      # Service-specific tests
  config.py                   # Service settings (pydantic-settings)
  main.py                     # FastAPI app entry point
infrastructure/terraform/     # IaC for cloud deployment
infrastructure/kubernetes/    # K8s manifests
database/schema.sql           # Canonical DB schema (source of truth)
database/seeds/               # Seed data SQL files
shared/                       # Cross-service reference patterns
docs/                         # API docs, sprint log, user guides
```

**Microservices:** auth, user, transaction, ledger, report, ai, notification, sync — each independently deployable with its own Dockerfile.

**Core database tables:** users, user_settings, accounts, transactions, categories, customers, ledger_entries, receipts (see `database/schema.sql`).

## Backend Coding Conventions

### Service Structure (follow for every new service)
Each service is **self-contained** for Docker (build context = `./services/<name>-service`). Shared patterns are consistent but each service carries its own copy.

Standard file layout for an implemented service:
```
config.py                     # Settings(BaseSettings) with env_prefix
db/session.py                 # async engine + get_db() dependency
db/__init__.py                # re-export get_db
models/base.py                # Base(DeclarativeBase)
models/<entity>.py            # ORM models matching database/schema.sql
schemas/<entity>.py           # Pydantic v2 request/response models
services/security.py          # JWT decode + get_current_user dependency
services/<entity>_service.py  # Business logic (no HTTP concerns)
routers/<entity>.py           # FastAPI router with endpoints
main.py                       # app = FastAPI(), include routers, /health
pytest.ini                    # asyncio_mode=auto, asyncio_default_fixture_loop_scope=session
tests/conftest.py             # SQLite test engine, session fixtures, auth helpers
tests/test_<entity>.py        # Test cases
```

### Async SQLAlchemy Patterns
- **Always use `populate_existing=True`** when re-querying after mutations to bust the identity map cache. Without this, stale relationship data causes `MissingGreenlet` errors during Pydantic serialization.
  ```python
  select(Model).options(selectinload(Model.rel)).where(...).execution_options(populate_existing=True)
  ```
- **Never rely on lazy loading** in async — always use `selectinload()` or `joinedload()` for relationships.
- **After flush, re-query** instead of `db.refresh()` when the response includes relationships or server-side defaults (`onupdate`, `server_default`).
- **`get_db()` pattern:** yield AsyncSession, commit on success, rollback on exception.

### Authentication
- **Password hashing:** Use `bcrypt` directly (`bcrypt.hashpw`/`bcrypt.checkpw`). Do NOT use `passlib` — it is incompatible with bcrypt>=5.0.
- **JWT:** Use `python-jose` with HS256. Tokens include a `type` claim (`"access"` or `"refresh"`) to prevent cross-use.
- **get_current_user dependency:** Each non-auth service implements its own in `services/security.py`, decoding JWT and loading the user from its own DB session.
- **Auth-required endpoints:** Use `current_user: User = Depends(get_current_user)` — no manual token parsing in routers.

### Role-Based Access Control (RBAC)

**Current roles:** `user` (all authenticated users) and `admin` (founders/ops via `is_admin` DB field or `ADMIN_EMAILS` env var).

**Rules for every new admin-only feature:**
1. **Server layer is mandatory.** Every admin API route must: (a) require `Authorization: Bearer <token>`, (b) call `resolveAdminStatus(token)` (proxy to auth-service `/auth/me`), (c) return `401` / `403` before returning any data.
2. **Fail closed.** Network error, timeout, or missing field → deny access. Never default to allow.
3. **`ADMIN_EMAILS` is server-only.** Never use `NEXT_PUBLIC_ADMIN_EMAILS` as an access control — it is a UX hint only (visible in the browser JS bundle).
4. **Client guards are UX only.** `isAdmin()` check in sidebar + `useEffect` redirect on the page are convenience, not security.
5. **User-scoped queries always.** Regular user routes must filter at the DB level by `user_id = current_user.id`. Never rely on application-layer filtering alone.

**Reference implementations:**
- Server admin check: `apps/web-dashboard/app/api/infra/costs/route.ts` — `resolveAdminStatus()`
- Client admin check: `apps/web-dashboard/lib/auth/is-admin.ts` — `isAdmin()`
- Sidebar nav gating: `apps/web-dashboard/components/layout/sidebar.tsx` — `adminOnly` flag
- Full checklist: `docs/developer/rbac-guide.md`
- User personas + permission matrix: `docs/product/user-personas.md`

### Pydantic Schemas
- Use `model_config = {"from_attributes": True}` for ORM conversion.
- Use `@field_validator` for business rules (password length, enum checks, ISO currency codes).
- Forward references between schemas require `ModelClass.model_rebuild()` after all classes are defined.

### Testing Conventions
- **Test DB:** SQLite + aiosqlite in-memory (`sqlite+aiosqlite:///:memory:`)
- **Session isolation:** Each test gets a fresh `engine.begin()` connection that rolls back after the test.
- **Auth in tests:** `make_access_token(user_id)` helper in conftest creates valid JWTs. `seed_user` + `auth_headers` fixtures provide authenticated context.
- **Dependency overrides:** Override `get_db` (and `get_redis` if used) in the `client` fixture. Clear overrides in teardown.
- **pytest.ini:** Always set `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = session`.
- **UUID column type:** Use `sqlalchemy.Uuid` (generic cross-dialect type) instead of `postgresql.UUID(as_uuid=True)` in ORM models. The PostgreSQL-specific type misinterprets deterministic UUID hex strings as scientific notation when running tests on SQLite with aiosqlite.

### General Rules
- ORM models must exactly match `database/schema.sql` column names and types.
- Use `uuid.uuid4()` for all new entity IDs.
- **UUID column type:** Always use `from sqlalchemy import Uuid` and `mapped_column(Uuid, ...)`. Never use `postgresql.UUID(as_uuid=True)` — it breaks on SQLite test backends (deterministic UUID hex with `e` gets misinterpreted as scientific notation).
- Use `Numeric(15, 2)` for all monetary amounts — never float.
- Soft-delete via `is_active=False` — never hard-delete user-facing records.
- Identical error messages for auth failures to prevent enumeration.
- All services share the same `jwt_secret` (via env vars) so tokens are cross-service valid.

## CI/CD

**Non-negotiable rules — these apply in every session, no exceptions:**
1. **Never commit directly to `main`.** All work happens on a sprint branch.
2. **`main` must always be green.** No merge unless all CI checks pass.
3. **No `--no-verify`, no skipping hooks.** Fix the root cause instead.
4. **Baseline (tag) `main` at every sprint merge:** `git tag sprint-<N>-done`.
5. **Test locally before pushing.** Run the relevant test suite before every push.
6. **Secrets never in code or tfvars.** Pass via `TF_VAR_*` env vars or GCP Secret Manager.

**GitHub Actions workflows (`.github/workflows/`):**
- `test.yml` — runs on push/PR to main. Uses `dorny/paths-filter` for change detection, then runs `pytest` only for modified services. SQLite test backend (no Postgres needed in CI).
- `lint.yml` — runs `ruff check` and `ruff format --check` across all services.
- `build.yml` — Docker build + push to GHCR (per-service, change detection).
- `deploy.yml` — manual deploy to staging/production via kubectl.

**Linting:**
- Config: `pyproject.toml` at repo root (ruff, Python 3.12 target, line-length 120).
- Rules: E (pycodestyle errors), F (pyflakes), I (isort), W (warnings). E501 (line too long) is ignored since line-length is 120.
- Run locally: `ruff check services/` and `ruff format --check services/`.
- Auto-fix formatting: `ruff format services/`.

**Makefile targets:**
- `make test-all` — run all 6 service test suites sequentially.
- `make test-<name>` — run a single service (e.g., `make test-auth`).
- `make lint` — check lint + format.
- `make format` — auto-format with ruff.

## Branching Strategy

**Trunk-based development with sprint branches.** `main` is the stable trunk.

```
main                          ← stable, always passing tests
 ├── sprint-0/auth            ← Sprint 0 work (merged → main)
 ├── sprint-1/user-shared     ← Sprint 1 work (merged → main)
 ├── sprint-2/transaction     ← Sprint 2 work (merged → main)
 ├── sprint-3/ledger          ← Sprint 3 work (merged → main)
 ├── sprint-4/report-notify   ← Sprint 4 work (merged → main)
 ├── retro-4.5/hardening      ← Retro 4.5 work (merged → main)
 └── sprint-5/sync-ai         ← current sprint branch
```

### Rules

1. **`main` is protected.** All tests must pass before merging. Never commit directly to `main`. Ever.
2. **One branch per sprint.** Named `sprint-<N>/<short-description>` (e.g., `sprint-5/sync-ai`). Retros use `retro-<N>/<description>`.
3. **Branch from `main` at sprint start.** This guarantees a clean, tested baseline.
4. **Merge to `main` at sprint end.** After all tests pass and docs are updated, merge (squash or regular) and tag: `git tag sprint-<N>-done`.
5. **Hotfix branches.** For urgent fixes between sprints: `hotfix/<description>`, branch from `main`, merge back to `main`.
6. **Baseline tagging.** Tag `main` after every sprint merge and every significant milestone. Tags are permanent baselines — never delete them.
7. **PR before merge.** Even solo — open a PR, let CI run, then merge. This keeps the audit trail clean.

### Commands

```bash
# Start a new sprint
git checkout main
git pull
git checkout -b sprint-<N>/<description>

# Before pushing — always run tests first
source .venv/bin/activate
for dir in services/*-service; do (cd "$dir" && python -m pytest tests/ -v --tb=short); done

# Push branch and open PR
git push -u origin sprint-<N>/<description>
gh pr create --title "Sprint <N>: <description>" --body "..."

# End a sprint — merge to main only after CI passes
git checkout main
git pull
git merge sprint-<N>/<description>
git tag sprint-<N>-done
git push && git push --tags
```

## Sprint Workflow

At the **start** of each sprint:
- Create a sprint branch from `main` (see Branching Strategy above)
- Read `MEMORY.md` for resume context (next sprint scope, endpoints, conventions)
- Read `ROADMAP.md` for the sprint checklist
- Read the relevant skeleton service to understand current state

At the **end** of each sprint:
- Run all service test suites to catch regressions
- Update `docs/SPRINT-LOG.md` with delivered endpoints, test counts, key decisions
- Update `docs/API.md` with full endpoint documentation for the new service
- Update `ROADMAP.md` current state table and mark the sprint as DONE
- Update `CLAUDE.md` project status line
- Save resume context to `MEMORY.md` — include: next sprint scope, planned endpoints, service conventions, any new patterns learned
- Merge sprint branch to `main` and tag (see Branching Strategy above)

**Parallel activities:** Documentation writing can run as a background agent while implementing code and tests.

## Planning Documents

Key technical references among the root-level markdown files:
- **Full Production System Blueprint.md** — microservices architecture, database design, infrastructure plan
- **LedgerLite Build Stack Deployment Kit.md** — code snippets (FastAPI, SQL, Docker, K8s, Terraform, Flutter, GitHub Actions, sklearn)
- **Founder Mode activated.md** — database schema, API contracts, sprint backlog
- **ROADMAP.md** — implementation roadmap with sprint breakdown and current status
