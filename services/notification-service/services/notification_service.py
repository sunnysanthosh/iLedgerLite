import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from models.customer import Customer
from models.ledger_entry import LedgerEntry
from models.notification import Notification
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_notifications(
    org_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
) -> tuple[list[Notification], int, int]:
    """Returns (notifications, total_count, unread_count)."""
    base = select(Notification).where(Notification.org_id == org_id)

    if unread_only:
        base = base.where(Notification.is_read.is_(False))

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Unread count (always total unread, regardless of filter)
    unread_q = select(func.count()).where(
        Notification.org_id == org_id,
        Notification.is_read.is_(False),
    )
    unread_result = await db.execute(unread_q)
    unread_count = unread_result.scalar() or 0

    # Fetch page
    items_q = base.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(items_q)
    notifications = list(result.scalars().all())

    return notifications, total, unread_count


async def mark_as_read(
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Notification:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalars().first()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = True
    await db.flush()

    # Re-query to get updated state
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id).execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def create_reminder(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    customer_id: uuid.UUID,
    custom_message: str | None,
    db: AsyncSession,
) -> Notification:
    """Create a credit reminder notification for a customer with outstanding balance."""
    # Verify customer belongs to org
    cust_result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.org_id == org_id))
    customer = cust_result.scalars().first()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Calculate outstanding balance
    balance_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((LedgerEntry.type == "debit", LedgerEntry.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_debit"),
            func.coalesce(
                func.sum(case((LedgerEntry.type == "credit", LedgerEntry.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_credit"),
        ).where(
            LedgerEntry.customer_id == customer_id,
            LedgerEntry.org_id == org_id,
            LedgerEntry.is_settled.is_(False),
        )
    )
    balances = balance_result.one()
    outstanding = balances.total_debit - balances.total_credit

    if outstanding <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer has no outstanding balance",
        )

    message = (
        custom_message
        or f"Reminder: {customer.name} has an outstanding balance of {outstanding:.2f}. Please follow up for payment."
    )

    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        org_id=org_id,
        type="reminder",
        title=f"Payment reminder for {customer.name}",
        message=message,
        related_entity_id=customer_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()
    return notification


async def create_system_notification(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str = "system",
    related_entity_id: uuid.UUID | None = None,
    db: AsyncSession = None,
) -> Notification:
    """Create a system/internal notification (e.g., org invite). No org-membership check."""
    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        org_id=org_id,
        type=notification_type,
        title=title,
        message=message,
        related_entity_id=related_entity_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()
    return notification
