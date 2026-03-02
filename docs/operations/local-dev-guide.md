# Local Development Guide

This guide covers everything needed to run LedgerLite locally for development and testing.
All services run in Docker Compose — no manual dependency installation required beyond
Docker Desktop and the Python venv (for running tests).

> See [environment-lifecycle.md](environment-lifecycle.md) for the on-demand philosophy
> that governs how and when to start/stop environments.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Python | 3.12.7 | `pyenv install 3.12.7` (`.python-version` sets this automatically) |
| GNU Make | Any | Pre-installed on macOS/Linux |
| ruff | Latest | `pip install ruff` in venv |

> Docker Desktop must be running before any `make dev-*` command.

---

## First-Time Setup

```bash
# 1. Clone the repo and enter it
git clone <repo-url>
cd iLedgerLite

# 2. Create the Python virtual environment (once per machine)
python -m venv .venv
source .venv/bin/activate

# 3. Install all service dependencies (for IDE support + running tests)
for req in services/*/requirements.txt; do pip install -r "$req"; done

# 4. Start the dev stack — Docker builds images and starts all services
make dev-start
```

On first run `make dev-start` will:
1. Pull base images (postgres:16-alpine, redis:7-alpine) — ~500 MB, one time only
2. Build all 8 service images from their Dockerfiles
3. Start Postgres, Redis, and all 8 services in the background
4. Apply `database/schema.sql` automatically (Postgres init script)
5. Wait for Postgres to be ready before exiting

---

## Daily Workflow

### Start of day

```bash
make dev-start
source .venv/bin/activate
```

### End of day

```bash
make dev-stop    # containers stop, volumes (data) preserved
deactivate
```

That is the entire lifecycle. Data in Postgres and Redis survives across `dev-stop` / `dev-start`
cycles because it lives in named Docker volumes (`postgres_data`, `redis_data`).

---

## All `make dev-*` Commands

### `make dev-start`
Start all services in the background and wait for Postgres to be ready.

```bash
make dev-start
# ==> Starting LedgerLite dev stack...
# ==> Waiting for Postgres to be ready...
# ✅ Dev stack is up. Services: auth=8001 user=8002 txn=8003 ...
```

**When to use:** Beginning of every dev session. Safe to run if services are already up
(`docker compose up -d` is idempotent).

### `make dev-stop`
Stop all containers. **Data volumes are preserved.**

```bash
make dev-stop
# ==> Stopping LedgerLite dev stack (data preserved)...
# ✅ Dev stack stopped. Data volumes intact. Run 'make dev-start' to resume.
```

**When to use:** End of every dev session. Frees CPU, RAM, and ports on your machine.

### `make dev-rebuild`
Full image rebuild followed by start. Equivalent to `docker compose up -d --build`.

```bash
make dev-rebuild
```

**When to use:**
- After modifying a `Dockerfile`
- After adding or removing packages in `requirements.txt`
- After a `git pull` that changes service code (normal code changes are hot-reloaded if
  `--reload` is configured, but a rebuild ensures images are current)

### `make dev-status`
Show the current state of all containers and their port bindings.

```bash
make dev-status
# NAME                    IMAGE               STATUS          PORTS
# iledgerlite-postgres-1  postgres:16-alpine  Up 2 hours      0.0.0.0:5432->5432/tcp
# iledgerlite-redis-1     redis:7-alpine      Up 2 hours      0.0.0.0:6379->6379/tcp
# iledgerlite-auth-...    ...                 Up 2 hours      0.0.0.0:8001->8000/tcp
# ...
```

### `make dev-logs`
Follow live logs from all services. Press `Ctrl-C` to stop.

```bash
make dev-logs

# For a single service only:
docker compose logs -f auth-service
```

### `make dev-reset`
**DESTRUCTIVE.** Removes all containers AND data volumes. Requires typing `yes` to confirm.

```bash
make dev-reset
# ⚠️  This will delete ALL local Postgres and Redis data.
# Type 'yes' to confirm: yes
# ✅ Full reset done. Run 'make dev-start' for a clean environment.
```

**When to use:**
- Postgres data is in an unrecoverable state
- You want a fresh schema apply (e.g., after a breaking migration change)
- Onboarding a new machine and starting clean

**What survives a reset:** Nothing in Postgres or Redis. Git history, source code, and
your `.venv` are untouched.

---

## Service Ports

| Service | Local port | Internal port |
|---|---|---|
| postgres | 5432 | 5432 |
| redis | 6379 | 6379 |
| auth-service | **8001** | 8000 |
| user-service | **8002** | 8000 |
| transaction-service | **8003** | 8000 |
| ledger-service | **8004** | 8000 |
| report-service | **8005** | 8000 |
| ai-service | **8006** | 8000 |
| notification-service | **8007** | 8000 |
| sync-service | **8008** | 8000 |

Health check for any service:
```bash
curl http://localhost:8001/health   # auth
curl http://localhost:8004/health   # ledger
# etc.
```

Interactive API docs (Swagger UI):
```
http://localhost:8001/docs   # auth-service
http://localhost:8002/docs   # user-service
# etc.
```

---

## Running Tests

Tests use SQLite in-memory — **no running Docker stack required** for unit tests.

```bash
# Activate venv first
source .venv/bin/activate

# Run all 8 service test suites
make test-all

# Run a single service
make test-auth
make test-transaction
# etc.

# Run with verbose output and stop at first failure
cd services/auth-service && python -m pytest tests/ -v -x

# Run a specific test
cd services/auth-service && python -m pytest tests/test_auth.py::test_login -v
```

---

## Linting and Formatting

```bash
# Check lint + format (CI gate — must pass before pushing)
make lint

# Auto-fix formatting
make format

# Lint a single service directory
ruff check services/auth-service/
```

Linting is enforced by the `lint.yml` GitHub Actions workflow. Fix all issues locally
before pushing to avoid a failed CI run.

---

## Connecting to Local Postgres

```bash
# psql via docker exec (no local psql install needed)
docker compose exec postgres psql -U ledgerlite -d ledgerlite

# Or using a local psql client
psql -h localhost -U ledgerlite -d ledgerlite
# Password: ledgerlite_dev (default for local)
```

Useful queries:
```sql
\dt                          -- list all tables
SELECT count(*) FROM users;
SELECT * FROM categories;
```

---

## Running a Single Service Outside Docker

Useful for faster iteration when working on one service:

```bash
# Ensure Docker stack is running (for Postgres + Redis)
make dev-start

# Activate venv
source .venv/bin/activate
cd services/auth-service
pip install -r requirements.txt

# Start with hot reload
AUTH_DATABASE_URL=postgresql://ledgerlite:ledgerlite_dev@localhost:5432/ledgerlite \
AUTH_REDIS_URL=redis://localhost:6379/0 \
AUTH_JWT_SECRET=dev-secret-change-me \
uvicorn main:app --reload --port 8001
```

The service running outside Docker connects to the Docker Compose Postgres/Redis via
the published ports (5432, 6379).

---

## Troubleshooting

### Ports already in use
```bash
# Find what is using port 5432
lsof -i :5432

# If a leftover container is the culprit
make dev-stop
make dev-start
```

### Service crashed / keeps restarting
```bash
make dev-status          # check which service is unhealthy
make dev-logs            # find the error
docker compose logs auth-service --tail=100
```

### Postgres container failed to start (corrupted volume)
```bash
# Nuclear option — wipes data and starts fresh
make dev-reset
make dev-start
```

### Images out of date after a git pull
```bash
make dev-rebuild
```

### Tests failing with import errors
```bash
# Ensure venv is activated and all deps installed
source .venv/bin/activate
for req in services/*/requirements.txt; do pip install -r "$req"; done
```

### `make dev-reset` prompt not appearing (non-interactive shell)
Run `docker compose down -v` directly instead — this is what `dev-reset` calls internally.

---

## Environment Variables (local defaults)

All env vars for local dev have safe defaults in `docker-compose.yml`.
You can override them by creating a `.env` file at the repo root:

```bash
# .env (git-ignored, do not commit)
POSTGRES_USER=ledgerlite
POSTGRES_PASSWORD=ledgerlite_dev
JWT_SECRET=dev-secret-change-me
```

> Never put real production secrets in `.env` or any committed file.
> Production secrets live exclusively in GitHub Environments + GCP Secret Manager.
