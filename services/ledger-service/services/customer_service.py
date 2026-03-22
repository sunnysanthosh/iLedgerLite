import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from models.customer import Customer
from models.ledger_entry import LedgerEntry
from schemas.customer import CustomerCreate, CustomerUpdate
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def _reload_customer(customer_id: uuid.UUID, db: AsyncSession) -> Customer:
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id).execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def _calculate_outstanding_balance(customer_id: uuid.UUID, db: AsyncSession) -> Decimal:
    """Outstanding = total debit - total credit (unsettled entries only)."""
    result = await db.execute(
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
            LedgerEntry.is_settled.is_(False),
        )
    )
    row = result.one()
    return row.total_debit - row.total_credit


async def create_customer(user_id: uuid.UUID, org_id: uuid.UUID, data: CustomerCreate, db: AsyncSession) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        user_id=user_id,
        org_id=org_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        address=data.address,
    )
    db.add(customer)
    await db.flush()
    return await _reload_customer(customer.id, db)


async def list_customers(
    org_id: uuid.UUID,
    db: AsyncSession,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[Customer, Decimal]], int]:
    base = select(Customer).where(Customer.org_id == org_id)

    if search:
        pattern = f"%{search}%"
        base = base.where(
            or_(
                Customer.name.ilike(pattern),
                Customer.phone.ilike(pattern),
                Customer.email.ilike(pattern),
            )
        )

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch page
    items_q = base.order_by(Customer.name).offset(skip).limit(limit)
    result = await db.execute(items_q)
    customers = list(result.scalars().all())

    # Attach outstanding balances
    customers_with_balance = []
    for c in customers:
        balance = await _calculate_outstanding_balance(c.id, db)
        customers_with_balance.append((c, balance))

    return customers_with_balance, total


async def get_customer(customer_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.org_id == org_id))
    customer = result.scalars().first()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


async def update_customer(
    customer_id: uuid.UUID, org_id: uuid.UUID, data: CustomerUpdate, db: AsyncSession
) -> Customer:
    customer = await get_customer(customer_id, org_id, db)

    if data.name is not None:
        customer.name = data.name
    if data.phone is not None:
        customer.phone = data.phone
    if data.email is not None:
        customer.email = data.email
    if data.address is not None:
        customer.address = data.address

    await db.flush()
    return await _reload_customer(customer.id, db)
