"""Add permissions column to org_memberships and backfill from role.

Revision ID: 008
Revises: 007
"""

import json

from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Permission presets — mirrors PERMISSION_PRESETS in user-service
# ---------------------------------------------------------------------------
_ALL_SCOPES = [
    "transactions:read", "transactions:write",
    "ledger:read", "ledger:write",
    "reports:read",
    "accounts:read", "accounts:write",
    "categories:read", "categories:write",
    "notifications:read",
    "sync:push",
    "members:read", "members:invite", "members:remove", "members:role_change",
    "org:read", "org:settings", "org:delete", "org:transfer",
    "audit:read",
]

_PRESETS = {
    "owner": _ALL_SCOPES,
    "member": [s for s in _ALL_SCOPES if s not in {
        "org:delete", "org:transfer",
        "members:remove", "members:role_change",
        "audit:read",
    }],
    "read_only": [s for s in _ALL_SCOPES if s.endswith(":read")],
    "accountant": [
        "transactions:read", "ledger:read", "ledger:write",
        "reports:read", "accounts:read", "audit:read",
    ],
    "staff": [
        "transactions:read", "transactions:write",
        "ledger:read", "ledger:write",
        "accounts:read",
    ],
}


def upgrade() -> None:
    op.add_column(
        "org_memberships",
        sa.Column("permissions", sa.Text(), nullable=False, server_default="[]"),
    )
    # Backfill from role
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, role FROM org_memberships")).fetchall()
    for row in rows:
        scopes = _PRESETS.get(row.role, _PRESETS["member"])
        conn.execute(
            sa.text("UPDATE org_memberships SET permissions = :p WHERE id = :id"),
            {"p": json.dumps(scopes), "id": str(row.id)},
        )


def downgrade() -> None:
    op.drop_column("org_memberships", "permissions")
