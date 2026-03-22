"""004 — organisations + org_memberships + org_id columns on data tables

Revision ID: 004
Revises: 003
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── New tables ────────────────────────────────────────────────────────────

    op.create_table(
        "organisations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.VARCHAR(255), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("is_personal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "org_memberships",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.VARCHAR(20),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'member', 'read_only')", name="org_memberships_role_check"),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_user"),
    )

    op.create_index("idx_org_memberships_org_id", "org_memberships", ["org_id"])
    op.create_index("idx_org_memberships_user_id", "org_memberships", ["user_id"])

    # ── Add org_id to existing data tables ───────────────────────────────────

    for table in ("accounts", "transactions", "categories", "customers", "ledger_entries", "notifications"):
        op.add_column(table, sa.Column("org_id", sa.UUID(), sa.ForeignKey("organisations.id"), nullable=True))

    op.create_index("idx_accounts_org_id", "accounts", ["org_id"])
    op.create_index("idx_transactions_org_id", "transactions", ["org_id"])
    op.create_index("idx_customers_org_id", "customers", ["org_id"])
    op.create_index("idx_ledger_entries_org_id", "ledger_entries", ["org_id"])


def downgrade() -> None:
    # Drop indexes on data tables
    op.drop_index("idx_ledger_entries_org_id", "ledger_entries")
    op.drop_index("idx_customers_org_id", "customers")
    op.drop_index("idx_transactions_org_id", "transactions")
    op.drop_index("idx_accounts_org_id", "accounts")

    # Drop org_id columns from data tables
    for table in ("notifications", "ledger_entries", "customers", "categories", "transactions", "accounts"):
        op.drop_column(table, "org_id")

    # Drop org tables
    op.drop_index("idx_org_memberships_user_id", "org_memberships")
    op.drop_index("idx_org_memberships_org_id", "org_memberships")
    op.drop_table("org_memberships")
    op.drop_table("organisations")
