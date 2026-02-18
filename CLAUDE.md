# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

LedgerLite is an **early-stage fintech SaaS product** — the monorepo scaffold is in place but feature development has not started. Planning documents (PRDs, investor briefs, architecture blueprints) are at the root level.

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
pytest tests/

# Apply database schema (requires running Postgres)
psql -h localhost -U ledgerlite -d ledgerlite -f database/schema.sql
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
  services/                   # Business logic
  db/                         # Database session, migrations
  tests/                      # Service-specific tests
  main.py                     # FastAPI app entry point
infrastructure/terraform/     # IaC for cloud deployment
infrastructure/kubernetes/    # K8s manifests
database/schema.sql           # Canonical DB schema
database/migrations/          # Alembic migrations
shared/                       # Cross-service utilities, models, configs
```

**Microservices:** auth, user, transaction, ledger, report, ai, notification, sync — each independently deployable with its own Dockerfile.

**Core database tables:** users, accounts, transactions, categories, customers, ledger_entries, receipts (see `database/schema.sql`).

## Planning Documents

Key technical references among the root-level markdown files:
- **Full Production System Blueprint.md** — microservices architecture, database design, infrastructure plan
- **🚀 LedgerLite Build Stack Deployment Kit.md** — code snippets (FastAPI, SQL, Docker, K8s, Terraform, Flutter, GitHub Actions, sklearn)
- **🚀Founder Mode activated.md** — database schema, API contracts, sprint backlog
