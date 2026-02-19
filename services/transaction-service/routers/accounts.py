from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from schemas.account import AccountCreate, AccountResponse, AccountUpdate
from services.account_service import (
    create_account,
    deactivate_account,
    get_account,
    list_accounts,
    update_account,
)
from services.security import get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_account(current_user.id, data, db)


@router.get("", response_model=list[AccountResponse])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_accounts(current_user.id, db)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_one(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    return await get_account(uuid.UUID(account_id), current_user.id, db)


@router.put("/{account_id}", response_model=AccountResponse)
async def update(
    account_id: str,
    data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    return await update_account(uuid.UUID(account_id), current_user.id, data, db)


@router.delete("/{account_id}", status_code=status.HTTP_200_OK)
async def deactivate(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    await deactivate_account(uuid.UUID(account_id), current_user.id, db)
    return {"detail": "Account deactivated"}
