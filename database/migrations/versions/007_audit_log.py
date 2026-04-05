"""007 — create audit_log table

Tracks org-level actions: member invite, role change, remove, org create.
Owned and written by user-service. Read via GET /organisations/{org_id}/audit.

Revision ID: 007
Revises: 006
Create Date: 2026-04-05
"""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.VARCHAR(50), nullable=False),
        sa.Column("entity_type", sa.VARCHAR(50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_log_org_id", "audit_log", ["org_id"])
    op.create_index("idx_audit_log_actor_id", "audit_log", ["actor_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_log_actor_id", "audit_log")
    op.drop_index("idx_audit_log_org_id", "audit_log")
    op.drop_table("audit_log")
