# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

LedgerLite is an **early-stage fintech SaaS product**. Backend microservices are under active development. Planning documents (PRDs, investor briefs, architecture blueprints) are at the root level. See `ROADMAP.md` for implementation status.

**Completed:** auth-service, user-service, transaction-service, ledger-service, report-service, notification-service, ai-service, sync-service, Alembic migrations, CI/CD (test + lint + build + deploy), Flutter mobile app MVP (auth, dashboard, transactions, accounts)
**In Progress:** —
**Not Started:** Kubernetes manifests (6B); Terraform IaC (6C); mobile ledger/reports/sync screens; web dashboard

## Build & Run Commands

```bash
# Start all services + Postgres + Redis
docker compose up --build

# Start a single service for development
cd services/<name>-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run tests for a single service
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
apps/mobile-app/              # Flutter (not yet scaffolded)
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

**GitHub Actions workflows (`.github/workflows/`):**
- `test.yml` — runs on push/PR to main. Uses `dorny/paths-filter` for change detection, then runs `pytest` only for modified services. SQLite test backend (no Postgres needed in CI).
- `lint.yml` — runs `ruff check` and `ruff format --check` across all services.

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

1. **`main` is protected.** All tests must pass before merging. Never commit directly to `main`.
2. **One branch per sprint.** Named `sprint-<N>/<short-description>` (e.g., `sprint-5/sync-ai`). Retros use `retro-<N>/<description>`.
3. **Branch from `main` at sprint start.** This guarantees a clean, tested baseline.
4. **Merge to `main` at sprint end.** After all tests pass and docs are updated, merge (squash or regular) and tag: `git tag sprint-<N>-done`.
5. **Hotfix branches.** For urgent fixes between sprints: `hotfix/<description>`, branch from `main`, merge back to `main`.

### Commands

```bash
# Start a new sprint
git checkout main
git pull                      # if remote exists
git checkout -b sprint-5/sync-ai

# End a sprint — merge to main
git checkout main
git merge sprint-5/sync-ai   # or: git merge --squash sprint-5/sync-ai
git tag sprint-5-done
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
