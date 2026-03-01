import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from models.account import Account
from schemas.account import AccountCreate, AccountUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _reload_account(account_id: uuid.UUID, db: AsyncSession) -> Account:
    result = await db.execute(select(Account).where(Account.id == account_id).execution_options(populate_existing=True))
    return result.scalars().first()


async def create_account(user_id: uuid.UUID, data: AccountCreate, db: AsyncSession) -> Account:
    account = Account(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        type=data.type,
        currency=data.currency,
        balance=Decimal("0.00"),
    )
    db.add(account)
    await db.flush()
    return await _reload_account(account.id, db)


async def list_accounts(user_id: uuid.UUID, db: AsyncSession) -> list[Account]:
    result = await db.execute(
        select(Account)
        .where(Account.user_id == user_id, Account.is_active.is_(True))
        .order_by(Account.created_at.desc())
    )
    return list(result.scalars().all())


async def get_account(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Account:
    result = await db.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


async def update_account(account_id: uuid.UUID, user_id: uuid.UUID, data: AccountUpdate, db: AsyncSession) -> Account:
    account = await get_account(account_id, user_id, db)

    if data.name is not None:
        account.name = data.name
    if data.type is not None:
        account.type = data.type

    await db.flush()
    return await _reload_account(account.id, db)


async def deactivate_account(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Account:
    account = await get_account(account_id, user_id, db)
    account.is_active = False
    await db.flush()
    return await _reload_account(account.id, db)
