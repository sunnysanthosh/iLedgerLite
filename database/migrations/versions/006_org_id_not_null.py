"""006 — enforce org_id NOT NULL on data tables

accounts, transactions, customers, ledger_entries, notifications.
categories is intentionally skipped — system categories have org_id IS NULL.

Migration 005 backfilled all user-owned rows, so no data loss.

Revision ID: 006
Revises: 005
Create Date: 2026-04-05
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

# Tables where org_id becomes mandatory (system-category table excluded)
_TABLES = ("accounts", "transactions", "customers", "ledger_entries", "notifications")


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(table, "org_id", existing_type=sa.UUID(), nullable=False)


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.alter_column(table, "org_id", existing_type=sa.UUID(), nullable=True)
