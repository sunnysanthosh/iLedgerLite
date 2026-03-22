import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from models.account import Account
from models.transaction import Transaction
from schemas.transaction import TransactionCreate, TransactionUpdate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def _reload_transaction(txn_id: uuid.UUID, db: AsyncSession) -> Transaction:
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id).execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def _verify_account_ownership(account_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Account:
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.org_id == org_id, Account.is_active.is_(True))
    )
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


async def _update_account_balance(
    account: Account, amount: Decimal, txn_type: str, reverse: bool, db: AsyncSession
) -> None:
    """Adjust account balance. If reverse=True, undo a previous transaction."""
    if reverse:
        if txn_type == "income":
            account.balance -= amount
        elif txn_type == "expense":
            account.balance += amount
    else:
        if txn_type == "income":
            account.balance += amount
        elif txn_type == "expense":
            account.balance -= amount
    await db.flush()


async def create_transaction(
    user_id: uuid.UUID, org_id: uuid.UUID, data: TransactionCreate, db: AsyncSession
) -> Transaction:
    account = await _verify_account_ownership(data.account_id, org_id, db)

    txn = Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        org_id=org_id,
        account_id=data.account_id,
        category_id=data.category_id,
        type=data.type,
        amount=data.amount,
        description=data.description,
        transaction_date=data.transaction_date,
    )
    db.add(txn)
    await _update_account_balance(account, data.amount, data.type, reverse=False, db=db)
    await db.flush()
    return await _reload_transaction(txn.id, db)


async def list_transactions(
    org_id: uuid.UUID,
    db: AsyncSession,
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    txn_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Transaction], int]:
    base = select(Transaction).where(Transaction.org_id == org_id)

    if account_id is not None:
        base = base.where(Transaction.account_id == account_id)
    if category_id is not None:
        base = base.where(Transaction.category_id == category_id)
    if txn_type is not None:
        base = base.where(Transaction.type == txn_type)
    if date_from is not None:
        base = base.where(Transaction.transaction_date >= date_from)
    if date_to is not None:
        base = base.where(Transaction.transaction_date <= date_to)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch page
    items_q = base.order_by(Transaction.transaction_date.desc()).offset(skip).limit(limit)
    result = await db.execute(items_q)
    items = list(result.scalars().all())

    return items, total


async def get_transaction(txn_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Transaction:
    result = await db.execute(select(Transaction).where(Transaction.id == txn_id, Transaction.org_id == org_id))
    txn = result.scalars().first()
    if txn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn


async def update_transaction(
    txn_id: uuid.UUID, org_id: uuid.UUID, data: TransactionUpdate, db: AsyncSession
) -> Transaction:
    txn = await get_transaction(txn_id, org_id, db)
    account = await _verify_account_ownership(txn.account_id, org_id, db)

    # Reverse old balance impact
    await _update_account_balance(account, txn.amount, txn.type, reverse=True, db=db)

    if data.type is not None:
        txn.type = data.type
    if data.amount is not None:
        txn.amount = data.amount
    if data.category_id is not None:
        txn.category_id = data.category_id
    if data.description is not None:
        txn.description = data.description
    if data.transaction_date is not None:
        txn.transaction_date = data.transaction_date

    # Apply new balance impact
    await _update_account_balance(account, txn.amount, txn.type, reverse=False, db=db)
    await db.flush()
    return await _reload_transaction(txn.id, db)


async def delete_transaction(txn_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> None:
    txn = await get_transaction(txn_id, org_id, db)
    account = await _verify_account_ownership(txn.account_id, org_id, db)

    # Reverse balance impact
    await _update_account_balance(account, txn.amount, txn.type, reverse=True, db=db)
    await db.delete(txn)
    await db.flush()
