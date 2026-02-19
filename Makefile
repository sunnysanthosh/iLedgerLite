SERVICES := auth-service user-service transaction-service ledger-service report-service notification-service ai-service sync-service

.PHONY: test-all test-auth test-user test-transaction test-ledger test-report test-notification test-ai test-sync lint format

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
