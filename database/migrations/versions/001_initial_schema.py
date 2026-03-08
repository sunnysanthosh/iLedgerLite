"""Initial schema — 10 tables matching database/schema.sql

Revision ID: 001
Revises: None
Create Date: 2026-02-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- user_settings ---
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column(
            "account_type",
            sa.String(20),
            server_default="personal",
            nullable=True,
        ),
        sa.Column("currency", sa.String(3), server_default="INR"),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("business_category", sa.String(100), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("account_type IN ('personal', 'business', 'both')", name="ck_user_settings_account_type"),
    )
    op.create_index("idx_user_settings_user_id", "user_settings", ["user_id"])

    # --- accounts ---
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR"),
        sa.Column("balance", sa.Numeric(15, 2), server_default="0.00"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('cash', 'bank', 'credit_card', 'wallet', 'loan')", name="ck_accounts_type"),
    )
    op.create_index("idx_accounts_user_id", "accounts", ["user_id"])

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('income', 'expense')", name="ck_categories_type"),
    )

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('income', 'expense', 'transfer')", name="ck_transactions_type"),
    )
    op.create_index("idx_transactions_user_id", "transactions", ["user_id"])
    op.create_index("idx_transactions_account_id", "transactions", ["account_id"])
    op.create_index("idx_transactions_date", "transactions", ["transaction_date"])

    # --- customers ---
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- ledger_entries ---
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("is_settled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('debit', 'credit')", name="ck_ledger_entries_type"),
    )
    op.create_index("idx_ledger_entries_user_id", "ledger_entries", ["user_id"])
    op.create_index("idx_ledger_entries_customer_id", "ledger_entries", ["customer_id"])

    # --- receipts ---
    op.create_table(
        "receipts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("related_entity_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "type IN ('reminder', 'payment', 'overdue', 'system')", name="ck_notifications_type"
        ),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])

    # --- sync_log ---
    op.create_table(
        "sync_log",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sync_status", sa.String(20), server_default="completed", nullable=False),
        sa.Column("changes_pushed", sa.Integer(), server_default="0"),
        sa.Column("changes_pulled", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "sync_status IN ('pending', 'in_progress', 'completed', 'failed')", name="ck_sync_log_status"
        ),
    )
    op.create_index("idx_sync_log_user_device", "sync_log", ["user_id", "device_id"])


def downgrade() -> None:
    op.drop_table("sync_log")
    op.drop_table("notifications")
    op.drop_table("user_settings")
    op.drop_table("receipts")
    op.drop_table("ledger_entries")
    op.drop_table("customers")
    op.drop_table("categories")
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("users")
