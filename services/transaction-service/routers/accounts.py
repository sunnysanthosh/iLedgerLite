import uuid

from db import get_db
from fastapi import APIRouter, Depends, status
from models.org import OrgMembership
from schemas.account import AccountCreate, AccountResponse, AccountUpdate
from services.account_service import (
    create_account,
    deactivate_account,
    get_account,
    list_accounts,
    update_account,
)
from services.security import get_org_member, get_write_member
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: AccountCreate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await create_account(membership.user_id, membership.org_id, data, db)


@router.get("", response_model=list[AccountResponse])
async def list_all(
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await list_accounts(membership.org_id, db)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_one(
    account_id: uuid.UUID,
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_account(account_id, membership.org_id, db)


@router.put("/{account_id}", response_model=AccountResponse)
async def update(
    account_id: uuid.UUID,
    data: AccountUpdate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await update_account(account_id, membership.org_id, data, db)


@router.delete("/{account_id}", status_code=status.HTTP_200_OK)
async def deactivate(
    account_id: uuid.UUID,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    await deactivate_account(account_id, membership.org_id, db)
    return {"detail": "Account deactivated"}
