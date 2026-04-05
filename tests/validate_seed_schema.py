"""
Schema Consistency Validator — CI Gate (Layer 4)

Verifies that shared/test_data.py seed collections are complete relative to
the NOT NULL columns declared on each seeded table. Catches the class of
failure where a sprint adds a NOT NULL column but forgets to backfill seed data.

Run:
    python tests/validate_seed_schema.py
Exit 0 = clean. Exit 1 = violations found (CI fails).
"""

import sys
from pathlib import Path

# Make shared/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "transaction-service"))  # for ORM models

from shared.test_data import (  # noqa: E402
    ACCOUNTS,
    ALL_CATEGORIES,
    CUSTOMERS,
    LEDGER_ENTRIES,
    ORG_MEMBERSHIPS,
    ORGANISATIONS,
    TRANSACTIONS,
    USERS,
    USER_SETTINGS,
)

# ---------------------------------------------------------------------------
# Define which fields are REQUIRED (NOT NULL, no server_default) per collection.
# Update this map whenever database/schema.sql changes a column to NOT NULL.
# ---------------------------------------------------------------------------
REQUIRED_FIELDS: dict[str, tuple[list[dict], list[str]]] = {
    "USERS": (
        USERS,
        ["id", "email", "password_hash", "full_name", "is_active"],
    ),
    "USER_SETTINGS": (
        USER_SETTINGS,
        ["id", "user_id"],
    ),
    "ORGANISATIONS": (
        ORGANISATIONS,
        ["id", "name", "owner_id", "is_personal", "is_active"],
    ),
    "ORG_MEMBERSHIPS": (
        ORG_MEMBERSHIPS,
        ["id", "org_id", "user_id", "role", "is_active"],
    ),
    "ACCOUNTS": (
        ACCOUNTS,
        ["id", "user_id", "org_id", "name", "type", "currency", "is_active"],
    ),
    "ALL_CATEGORIES": (
        ALL_CATEGORIES,
        ["id", "name", "type", "is_system"],
    ),
    "TRANSACTIONS": (
        TRANSACTIONS,
        ["id", "user_id", "org_id", "account_id", "type", "amount", "transaction_date"],
    ),
    "CUSTOMERS": (
        CUSTOMERS,
        ["id", "user_id", "org_id", "name"],
    ),
    "LEDGER_ENTRIES": (
        LEDGER_ENTRIES,
        ["id", "user_id", "org_id", "customer_id", "type", "amount", "is_settled"],
    ),
}

# ---------------------------------------------------------------------------
# Cross-reference checks: every foreign key value must exist in the referenced list
# ---------------------------------------------------------------------------
_user_ids = {u["id"] for u in USERS}
_org_ids = {o["id"] for o in ORGANISATIONS}
_account_ids = {a["id"] for a in ACCOUNTS}
_customer_ids = {c["id"] for c in CUSTOMERS}

FK_CHECKS: list[tuple[str, list[dict], str, set]] = [
    ("ACCOUNTS.user_id", ACCOUNTS, "user_id", _user_ids),
    ("ACCOUNTS.org_id", ACCOUNTS, "org_id", _org_ids),
    ("TRANSACTIONS.user_id", TRANSACTIONS, "user_id", _user_ids),
    ("TRANSACTIONS.org_id", TRANSACTIONS, "org_id", _org_ids),
    ("TRANSACTIONS.account_id", TRANSACTIONS, "account_id", _account_ids),
    ("CUSTOMERS.user_id", CUSTOMERS, "user_id", _user_ids),
    ("CUSTOMERS.org_id", CUSTOMERS, "org_id", _org_ids),
    ("LEDGER_ENTRIES.user_id", LEDGER_ENTRIES, "user_id", _user_ids),
    ("LEDGER_ENTRIES.org_id", LEDGER_ENTRIES, "org_id", _org_ids),
    ("LEDGER_ENTRIES.customer_id", LEDGER_ENTRIES, "customer_id", _customer_ids),
    ("ORGANISATIONS.owner_id", ORGANISATIONS, "owner_id", _user_ids),
    ("ORG_MEMBERSHIPS.org_id", ORG_MEMBERSHIPS, "org_id", _org_ids),
    ("ORG_MEMBERSHIPS.user_id", ORG_MEMBERSHIPS, "user_id", _user_ids),
]

# ---------------------------------------------------------------------------
# USER_ORG_MAP coverage: every active user must have exactly one personal org
# ---------------------------------------------------------------------------
from shared.test_data import USER_ORG_MAP  # noqa: E402

# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

violations: list[str] = []


def check_required_fields() -> None:
    for collection_name, (items, required) in REQUIRED_FIELDS.items():
        if not items:
            violations.append(f"{collection_name}: collection is empty")
            continue
        for i, item in enumerate(items):
            for field in required:
                if field not in item:
                    violations.append(
                        f"{collection_name}[{i}] (id={item.get('id', '?')}): "
                        f"missing required field '{field}'"
                    )
                elif item[field] is None:
                    violations.append(
                        f"{collection_name}[{i}] (id={item.get('id', '?')}): "
                        f"field '{field}' is None (NOT NULL violation)"
                    )


def check_foreign_keys() -> None:
    for label, items, field, valid_ids in FK_CHECKS:
        for i, item in enumerate(items):
            val = item.get(field)
            if val is not None and str(val) not in valid_ids:
                violations.append(
                    f"FK violation {label}: item[{i}] (id={item.get('id', '?')}) "
                    f"references unknown {field}='{val}'"
                )


def check_org_coverage() -> None:
    """Every active user must have a personal org in USER_ORG_MAP and ORGANISATIONS."""
    active_users = {u["id"] for u in USERS if u.get("is_active")}
    personal_org_ids = {o["id"] for o in ORGANISATIONS if o.get("is_personal")}
    personal_org_owners = {o["owner_id"] for o in ORGANISATIONS if o.get("is_personal")}

    for user_id in active_users:
        if user_id not in USER_ORG_MAP:
            violations.append(f"USER_ORG_MAP: active user '{user_id}' has no personal org mapping")
        if user_id not in personal_org_owners:
            violations.append(f"ORGANISATIONS: active user '{user_id}' has no personal org row")

    for user_id, org_id in USER_ORG_MAP.items():
        if org_id not in personal_org_ids:
            violations.append(
                f"USER_ORG_MAP: maps user '{user_id}' → org '{org_id}' "
                f"but that org is not in ORGANISATIONS with is_personal=True"
            )


def check_org_membership_coverage() -> None:
    """Every org must have at least one owner membership."""
    org_owners: dict[str, list] = {}
    for m in ORG_MEMBERSHIPS:
        org_id = m.get("org_id", "")
        if m.get("role") == "owner" and m.get("is_active"):
            org_owners.setdefault(org_id, []).append(m)

    for org in ORGANISATIONS:
        if not org_owners.get(org["id"]):
            violations.append(
                f"ORG_MEMBERSHIPS: org '{org['id']}' ({org.get('name')}) "
                f"has no active owner membership"
            )


check_required_fields()
check_foreign_keys()
check_org_coverage()
check_org_membership_coverage()

if violations:
    print(f"\nSeed schema validation FAILED — {len(violations)} violation(s):\n")
    for v in violations:
        print(f"  ✗ {v}")
    print(
        "\nFix: update shared/test_data.py to satisfy all NOT NULL and FK constraints.\n"
        "See docs/developer/schema-change-checklist.md for the sprint checklist.\n"
    )
    sys.exit(1)
else:
    total = sum(len(items) for items, _ in REQUIRED_FIELDS.values())
    print(f"Seed schema validation passed — {total} rows across {len(REQUIRED_FIELDS)} collections, all constraints satisfied.")
    sys.exit(0)
