# LedgerLite

Mobile-first accounting and ledger platform for households and small businesses, targeting the India/SEA market.

## Architecture

8 Python microservices built with FastAPI, backed by PostgreSQL and Redis.

| Service | Port | Description |
|---------|------|-------------|
| auth-service | 8001 | JWT registration, login, token refresh |
| user-service | 8002 | Profiles, onboarding, settings |
| transaction-service | 8003 | Accounts, categories, transactions with balance tracking |
| ledger-service | 8004 | Customer credit/debit tracking for shop owners |
| report-service | 8005 | Profit-loss, cashflow, budget, CSV export |
| ai-service | 8006 | Transaction categorization, spending insights, OCR stub |
| notification-service | 8007 | Payment reminders, notification management |
| sync-service | 8008 | Offline-first sync with conflict resolution |

```
services/
  auth-service/         user-service/          transaction-service/
  ledger-service/       report-service/        ai-service/
  notification-service/ sync-service/
database/
  schema.sql            seeds/
infrastructure/
  kubernetes/           terraform/
apps/
  mobile-app/           web-dashboard/
```

## Quick Start

### Docker (all services)

```bash
docker compose up --build
```

Services start on ports 8001-8008. PostgreSQL on 5432, Redis on 6379.

### Single service (development)

```bash
cd services/auth-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Database

```bash
psql -h localhost -U ledgerlite -d ledgerlite -f database/schema.sql
```

## Testing

All tests run against SQLite in-memory (no Postgres required).

```bash
# All services (146 tests)
make test-all

# Individual service
make test-auth
make test-transaction
make test-ledger
# ... etc

# Or directly
cd services/auth-service && python -m pytest tests/ -v
```

## Linting

Uses [ruff](https://docs.astral.sh/ruff/) (Python 3.12, line-length 120).

```bash
make lint       # check
make format     # auto-fix
```

## CI/CD

GitHub Actions run on push/PR to `main`:

- **test.yml** -- per-service test matrix with change detection
- **lint.yml** -- ruff check + format check

## Documentation

| Document | Description |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Mermaid diagrams — system context, service mesh, data flow, auth, infra, ER |
| [docs/API.md](docs/API.md) | Full endpoint reference with request/response examples |
| [docs/SPRINT-LOG.md](docs/SPRINT-LOG.md) | Sprint history and delivered features |
| [ROADMAP.md](ROADMAP.md) | Implementation roadmap and status |

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), Pydantic v2
- **Database:** PostgreSQL 16, Redis 7
- **Auth:** JWT (HS256) with refresh token rotation
- **Testing:** pytest + httpx + aiosqlite
- **Linting:** ruff
- **Containers:** Docker Compose
- **CI:** GitHub Actions

## Project Status

All 8 backend microservices are complete with 146 tests passing. See [ROADMAP.md](ROADMAP.md) for the full implementation plan and [docs/SPRINT-LOG.md](docs/SPRINT-LOG.md) for sprint history.

**Next:** Sprint 6C (Terraform IaC) or Phase 2 growth features (OTP login, bank SMS parsing, UPI).

## License

Proprietary. All rights reserved.
