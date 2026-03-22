import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from models.customer import Customer
from models.ledger_entry import LedgerEntry
from schemas.ledger import LedgerEntryCreate, LedgerEntryUpdate
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def _reload_entry(entry_id: uuid.UUID, db: AsyncSession) -> LedgerEntry:
    result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.id == entry_id).execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def _verify_customer_org(customer_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.org_id == org_id))
    customer = result.scalars().first()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


async def create_ledger_entry(
    user_id: uuid.UUID, org_id: uuid.UUID, data: LedgerEntryCreate, db: AsyncSession
) -> LedgerEntry:
    await _verify_customer_org(data.customer_id, org_id, db)

    entry = LedgerEntry(
        id=uuid.uuid4(),
        user_id=user_id,
        org_id=org_id,
        customer_id=data.customer_id,
        type=data.type,
        amount=data.amount,
        description=data.description,
        due_date=data.due_date,
    )
    db.add(entry)
    await db.flush()
    return await _reload_entry(entry.id, db)


async def get_ledger_history(
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[LedgerEntry], int, Decimal, Decimal, Decimal]:
    """Returns (entries, total, total_debit, total_credit, outstanding_balance)."""
    await _verify_customer_org(customer_id, org_id, db)

    base = select(LedgerEntry).where(
        LedgerEntry.customer_id == customer_id,
        LedgerEntry.org_id == org_id,
    )

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch page
    items_q = base.order_by(LedgerEntry.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(items_q)
    entries = list(result.scalars().all())

    # Totals (across all entries, not just page)
    totals_result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.type == "debit", LedgerEntry.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_debit"),
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.type == "credit", LedgerEntry.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_credit"),
        ).where(
            LedgerEntry.customer_id == customer_id,
            LedgerEntry.org_id == org_id,
            LedgerEntry.is_settled.is_(False),
        )
    )
    totals = totals_result.one()
    total_debit = totals.total_debit
    total_credit = totals.total_credit
    outstanding = total_debit - total_credit

    return entries, total, total_debit, total_credit, outstanding


async def update_ledger_entry(
    entry_id: uuid.UUID, org_id: uuid.UUID, data: LedgerEntryUpdate, db: AsyncSession
) -> LedgerEntry:
    result = await db.execute(select(LedgerEntry).where(LedgerEntry.id == entry_id, LedgerEntry.org_id == org_id))
    entry = result.scalars().first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger entry not found")

    if data.amount is not None:
        entry.amount = data.amount
    if data.type is not None:
        entry.type = data.type
    if data.description is not None:
        entry.description = data.description
    if data.due_date is not None:
        entry.due_date = data.due_date
    if data.is_settled is not None:
        entry.is_settled = data.is_settled

    await db.flush()
    return await _reload_entry(entry.id, db)
