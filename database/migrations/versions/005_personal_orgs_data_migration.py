"""005 — create personal org per user + backfill org_id on all data tables

Every existing user gets one personal organisation automatically.
All their existing data rows are reassigned to that personal org.
New users will have a personal org created at registration (auth-service).

Revision ID: 005
Revises: 004
Create Date: 2026-03-22
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: create one personal org per existing user
    op.execute("""
        INSERT INTO organisations (id, name, owner_id, is_personal)
        SELECT
            gen_random_uuid(),
            full_name || '''s Personal',
            id,
            TRUE
        FROM users
    """)

    # Step 2: create owner membership for each personal org
    op.execute("""
        INSERT INTO org_memberships (org_id, user_id, role)
        SELECT o.id, o.owner_id, 'owner'
        FROM organisations o
        WHERE o.is_personal = TRUE
    """)

    # Step 3: backfill org_id on data tables using user → personal org mapping
    op.execute("""
        UPDATE accounts a
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = a.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE a.org_id IS NULL
    """)

    op.execute("""
        UPDATE transactions t
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = t.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE t.org_id IS NULL
    """)

    op.execute("""
        UPDATE categories c
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = c.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE c.user_id IS NOT NULL AND c.org_id IS NULL
    """)

    op.execute("""
        UPDATE customers cu
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = cu.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE cu.org_id IS NULL
    """)

    op.execute("""
        UPDATE ledger_entries le
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = le.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE le.org_id IS NULL
    """)

    op.execute("""
        UPDATE notifications n
        SET org_id = (
            SELECT o.id FROM organisations o
            WHERE o.owner_id = n.user_id AND o.is_personal = TRUE
            LIMIT 1
        )
        WHERE n.org_id IS NULL
    """)


def downgrade() -> None:
    # Clear org_id from all data tables
    for table in ("notifications", "ledger_entries", "customers", "categories", "transactions", "accounts"):
        op.execute(f"UPDATE {table} SET org_id = NULL")  # noqa: S608

    # Remove personal org memberships and orgs
    op.execute("DELETE FROM org_memberships WHERE org_id IN (SELECT id FROM organisations WHERE is_personal = TRUE)")
    op.execute("DELETE FROM organisations WHERE is_personal = TRUE")
