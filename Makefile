SERVICES := auth-service user-service transaction-service ledger-service report-service notification-service ai-service sync-service

.PHONY: test-all test-auth test-user test-transaction test-ledger test-report test-notification test-ai test-sync lint format \
        dev-start dev-stop dev-rebuild dev-status dev-logs dev-reset

# ---------------------------------------------------------------------------
# Dev environment — start/stop Docker Compose stack (mirrors staging on-demand model)
# ---------------------------------------------------------------------------

## dev-start: Start all services in the background and wait for Postgres to be ready.
## Equivalent to `staging-start.yml` (wake infra before a dev/test session).
dev-start:
	@echo "==> Starting LedgerLite dev stack..."
	docker compose up -d
	@echo "==> Waiting for Postgres to be ready..."
	@for i in $$(seq 1 20); do \
		docker compose exec -T postgres pg_isready -U ledgerlite -q 2>/dev/null && break; \
		echo "  Postgres not ready yet (attempt $$i/20)..."; \
		sleep 2; \
	done
	@docker compose exec -T postgres pg_isready -U ledgerlite -q \
		&& echo "✅ Dev stack is up. Services: auth=8001 user=8002 txn=8003 ledger=8004 report=8005 ai=8006 notify=8007 sync=8008" \
		|| (echo "❌ Postgres never became ready" && exit 1)

## dev-stop: Stop all containers but PRESERVE data volumes (Postgres + Redis data safe).
## Run this at end of day. Equivalent to `staging-stop.yml` (scale to 0, no waste).
dev-stop:
	@echo "==> Stopping LedgerLite dev stack (data preserved)..."
	docker compose stop
	@echo "✅ Dev stack stopped. Data volumes intact. Run 'make dev-start' to resume."

## dev-rebuild: Full image rebuild + start. Use after changing a Dockerfile or requirements.txt.
dev-rebuild:
	@echo "==> Rebuilding and starting LedgerLite dev stack..."
	docker compose up -d --build
	@echo "✅ Dev stack rebuilt and started."

## dev-status: Show running containers and their ports.
dev-status:
	docker compose ps

## dev-logs: Tail logs for all services (Ctrl-C to stop).
dev-logs:
	docker compose logs --tail=50 -f

## dev-reset: DESTRUCTIVE — remove containers AND data volumes. Dev reset only.
## Use when you need a clean-slate Postgres (re-runs schema init on next dev-start).
dev-reset:
	@echo "⚠️  This will delete ALL local Postgres and Redis data."
	@printf "Type 'yes' to confirm: "; read confirm; [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	docker compose down -v
	@echo "✅ Full reset done. Run 'make dev-start' for a clean environment."

test-all:
	@for svc in $(SERVICES); do \
		echo "\n===== Testing $$svc ====="; \
		(cd services/$$svc && python -m pytest tests/ -v) || exit 1; \
	done

test-auth:
	cd services/auth-service && python -m pytest tests/ -v

test-user:
	cd services/user-service && python -m pytest tests/ -v

test-transaction:
	cd services/transaction-service && python -m pytest tests/ -v

test-ledger:
	cd services/ledger-service && python -m pytest tests/ -v

test-report:
	cd services/report-service && python -m pytest tests/ -v

test-notification:
	cd services/notification-service && python -m pytest tests/ -v

test-ai:
	cd services/ai-service && python -m pytest tests/ -v

test-sync:
	cd services/sync-service && python -m pytest tests/ -v

lint:
	ruff check services/
	ruff format --check services/

format:
	ruff format services/
