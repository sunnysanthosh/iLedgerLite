"""Seed 29 system categories (8 income + 21 expense)

Revision ID: 002
Revises: 001
Create Date: 2026-02-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INCOME_CATEGORIES = [
    ("Salary", "briefcase"),
    ("Freelance", "laptop"),
    ("Business Income", "store"),
    ("Investment Returns", "trending-up"),
    ("Rental Income", "home"),
    ("Gift Received", "gift"),
    ("Refund", "rotate-ccw"),
    ("Other Income", "plus-circle"),
]

EXPENSE_CATEGORIES = [
    ("Food & Dining", "utensils"),
    ("Groceries", "shopping-cart"),
    ("Transport", "car"),
    ("Fuel", "fuel"),
    ("Rent", "home"),
    ("Utilities", "zap"),
    ("Mobile & Internet", "smartphone"),
    ("Shopping", "shopping-bag"),
    ("Healthcare", "heart"),
    ("Education", "book"),
    ("Entertainment", "film"),
    ("Travel", "map"),
    ("Insurance", "shield"),
    ("EMI / Loan Payment", "credit-card"),
    ("Subscription", "repeat"),
    ("Gift / Donation", "gift"),
    ("Taxes", "file-text"),
    ("Maintenance", "tool"),
    ("Salary Expense", "users"),
    ("Supplier Payment", "truck"),
    ("Other Expense", "minus-circle"),
]


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("type", sa.String()),
        sa.column("icon", sa.String()),
        sa.column("is_system", sa.Boolean()),
    )

    rows = []
    for name, icon in INCOME_CATEGORIES:
        rows.append({"user_id": None, "name": name, "type": "income", "icon": icon, "is_system": True})
    for name, icon in EXPENSE_CATEGORIES:
        rows.append({"user_id": None, "name": name, "type": "expense", "icon": icon, "is_system": True})

    op.bulk_insert(categories, rows)


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE is_system = true")
