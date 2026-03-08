"""Add missing FK indexes

Revision ID: 003
Revises: 002
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_categories_user_id", "categories", ["user_id"])
    op.create_index(
        "idx_transactions_category_id",
        "transactions",
        ["category_id"],
        postgresql_where="category_id IS NOT NULL",
    )
    op.create_index("idx_customers_user_id", "customers", ["user_id"])
    op.create_index("idx_receipts_transaction_id", "receipts", ["transaction_id"])


def downgrade() -> None:
    op.drop_index("idx_receipts_transaction_id", table_name="receipts")
    op.drop_index("idx_customers_user_id", table_name="customers")
    op.drop_index("idx_transactions_category_id", table_name="transactions")
    op.drop_index("idx_categories_user_id", table_name="categories")
