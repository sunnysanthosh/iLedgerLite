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


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO categories (user_id, name, type, icon, is_system)
        SELECT NULL, v.name, v.type::VARCHAR, v.icon, true
        FROM (VALUES
            ('Salary', 'income', 'briefcase'),
            ('Freelance', 'income', 'laptop'),
            ('Business Income', 'income', 'store'),
            ('Investment Returns', 'income', 'trending-up'),
            ('Rental Income', 'income', 'home'),
            ('Gift Received', 'income', 'gift'),
            ('Refund', 'income', 'rotate-ccw'),
            ('Other Income', 'income', 'plus-circle'),
            ('Food & Dining', 'expense', 'utensils'),
            ('Groceries', 'expense', 'shopping-cart'),
            ('Transport', 'expense', 'car'),
            ('Fuel', 'expense', 'fuel'),
            ('Rent', 'expense', 'home'),
            ('Utilities', 'expense', 'zap'),
            ('Mobile & Internet', 'expense', 'smartphone'),
            ('Shopping', 'expense', 'shopping-bag'),
            ('Healthcare', 'expense', 'heart'),
            ('Education', 'expense', 'book'),
            ('Entertainment', 'expense', 'film'),
            ('Travel', 'expense', 'map'),
            ('Insurance', 'expense', 'shield'),
            ('EMI / Loan Payment', 'expense', 'credit-card'),
            ('Subscription', 'expense', 'repeat'),
            ('Gift / Donation', 'expense', 'gift'),
            ('Taxes', 'expense', 'file-text'),
            ('Maintenance', 'expense', 'tool'),
            ('Salary Expense', 'expense', 'users'),
            ('Supplier Payment', 'expense', 'truck'),
            ('Other Expense', 'expense', 'minus-circle')
        ) AS v(name, type, icon)
        WHERE NOT EXISTS (
            SELECT 1 FROM categories
            WHERE name = v.name AND type = v.type::VARCHAR AND is_system = true
        )
    """))


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE is_system = true")
