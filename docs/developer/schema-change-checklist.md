# Schema Change Checklist

Every sprint that adds, removes, or tightens a database column must work through
this checklist before opening a PR. These are the exact classes of failure that
caused post-sprint test breakage and are now enforced by CI gates.

---

## When to use this checklist

Use whenever a sprint:
- Adds a new column (nullable or NOT NULL)
- Changes a nullable column to NOT NULL
- Adds a new table that stores application data
- Removes or renames a column

---

## The checklist

### 1. ORM models — all services that read this table

For each service that has a model for the changed table:

- [ ] `org_id: Mapped[uuid.UUID | None]` → `Mapped[uuid.UUID]` if making NOT NULL
- [ ] Column added to all model files, not just the owning service
- [ ] Read-only ORM copies (report, ai, sync) updated the same way

**Files to touch:** every `services/*/models/<table>.py` that declares the changed column.

---

### 2. shared/test_data.py — centralized seed data

This file is the single source of truth for all smoke and regression tests.
Missing a column here breaks 3 CI layers at once.

- [ ] New column added to **every dict** in the relevant list
  (ACCOUNTS, TRANSACTIONS, CUSTOMERS, LEDGER_ENTRIES, etc.)
- [ ] If the column references another table, the FK value points to a valid row
  in the referenced list (e.g., `org_id` must be in ORGANISATIONS)
- [ ] If a new table is introduced, add a new top-level list
  (e.g., ORGANISATIONS, ORG_MEMBERSHIPS) with one row per relevant entity
- [ ] If org-scoped, add `"org_id": USER_ORG_MAP[user_id]` — or use the
  module-level backfill pattern at the bottom of the file
- [ ] Run `python tests/validate_seed_schema.py` — must exit 0

---

### 3. tests/conftest.py — root-level fixture infrastructure

The root conftest constructs ORM objects for smoke and regression tests.
Any new NOT NULL column must be passed in every relevant constructor call.

- [ ] New column added to ORM constructor calls for affected tables
  (Account, Transaction, Customer, LedgerEntry, etc.)
- [ ] If a new table is introduced, add its model import and seed loop
- [ ] If new org tables are added, include in `create_all_tables` model list
- [ ] Auth header fixtures include `X-Org-ID` if org-scoped endpoint changed

**Affected fixture functions:**
- `seeded_txn_client` → Account, Transaction
- `seeded_ledger_client` → Customer, LedgerEntry
- `seeded_user_client` → User, UserSettings
- `create_all_tables` → model module import list

---

### 4. Service conftest files — per-service fixture infrastructure

Each service has its own `tests/conftest.py`. These run the unit test suite.

- [ ] `seed_user` fixture seeds org + membership if service is org-scoped
- [ ] `auth_headers` fixture includes `X-Org-ID`
- [ ] New model columns added to all ORM constructors in fixture helpers
- [ ] `read_only_headers` fixture present if service has write-protected endpoints

---

### 5. Alembic migration

- [ ] `database/migrations/versions/<N>_<description>.py` created
- [ ] `upgrade()` makes the schema change
- [ ] `downgrade()` reverses it cleanly
- [ ] `database/schema.sql` updated to match (source of truth)
- [ ] Migration tested: `alembic upgrade head` on a clean DB

---

### 6. API docs

- [ ] `docs/API.md` updated if the change affects request/response shapes
- [ ] New endpoint documented with method, path, status codes, auth requirements

---

## CI gate map

| Gate | What it catches | Triggered by |
|---|---|---|
| **Layer 1** — service unit tests | Service-level logic breaks, ORM mismatches | Changed service paths |
| **Layer 2** — smoke tests | ASGI client setup failures, basic endpoint correctness | Every PR |
| **Layer 3** — regression tests | Data isolation breaks, cross-service business rules | Every PR |
| **Layer 4** — schema validator | Seed data missing NOT NULL fields, broken FK references | Every PR |
| **all-tests-passed** | Sprint merge gate — all 4 layers required | Every PR to main |

All four layers are required to pass before a PR can be merged to `main`.

Run locally before pushing:
```bash
make test-e2e
```

---

## Common failure patterns and fixes

### `NOT NULL constraint failed: <table>.<column>`
**Root cause:** New NOT NULL column missing from seed data or fixture constructors.
**Fix:** Steps 2 + 3 above.

### `403 Not a member of this organisation`
**Root cause:** `get_org_member` can't find a membership row; org not seeded,
or `X-Org-ID` header missing from test auth headers.
**Fix:** Steps 3 + 4 above (seed organisations + memberships, add header).

### `MissingGreenlet` / lazy load error
**Root cause:** ORM relationship accessed outside async context.
**Fix:** Use `selectinload()` + `populate_existing=True` on the query.

### Smoke test passes, regression test fails
**Root cause:** Seed data has correct structure but wrong values
(wrong count, wrong type, wrong FK).
**Fix:** Audit the relevant list in `shared/test_data.py` against the assertions
in `tests/regression/`.
