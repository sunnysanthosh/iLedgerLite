import uuid
from datetime import datetime

from db import get_db
from fastapi import APIRouter, Depends, Query, status
from models.org import OrgMembership
from schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from services.security import get_org_member, get_write_member
from services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: TransactionCreate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await create_transaction(membership.user_id, membership.org_id, data, db)


@router.get("", response_model=TransactionListResponse)
async def list_all(
    account_id: uuid.UUID | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    type: str | None = Query(None, description="income, expense, or transfer"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_transactions(
        membership.org_id,
        db,
        account_id=account_id,
        category_id=category_id,
        txn_type=type,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_one(
    transaction_id: uuid.UUID,
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_transaction(transaction_id, membership.org_id, db)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await update_transaction(transaction_id, membership.org_id, data, db)


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
async def delete(
    transaction_id: uuid.UUID,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    await delete_transaction(transaction_id, membership.org_id, db)
    return {"detail": "Transaction deleted"}
