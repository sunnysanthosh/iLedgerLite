"""Permission preset definitions.

Each preset maps to an explicit list of scope strings stored on org_memberships.permissions.
New scopes can be added here without a schema migration.
"""

ALL_SCOPES: list[str] = [
    "transactions:read",
    "transactions:write",
    "ledger:read",
    "ledger:write",
    "reports:read",
    "accounts:read",
    "accounts:write",
    "categories:read",
    "categories:write",
    "notifications:read",
    "sync:push",
    "members:read",
    "members:invite",
    "members:remove",
    "members:role_change",
    "org:read",
    "org:settings",
    "org:delete",
    "org:transfer",
    "audit:read",
]

VALID_ROLES: set[str] = {"owner", "member", "read_only", "accountant", "staff"}

PERMISSION_PRESETS: dict[str, list[str]] = {
    "owner": ALL_SCOPES,
    "member": [
        s
        for s in ALL_SCOPES
        if s
        not in {
            "org:delete",
            "org:transfer",
            "members:remove",
            "members:role_change",
            "audit:read",
        }
    ],
    "read_only": [s for s in ALL_SCOPES if s.endswith(":read")],
    "accountant": [
        "transactions:read",
        "ledger:read",
        "ledger:write",
        "reports:read",
        "accounts:read",
        "audit:read",
    ],
    "staff": [
        "transactions:read",
        "transactions:write",
        "ledger:read",
        "ledger:write",
        "accounts:read",
    ],
}


def resolve_permissions(role: str) -> list[str]:
    """Return the scope list for a given role preset name."""
    return PERMISSION_PRESETS.get(role, PERMISSION_PRESETS["member"])
