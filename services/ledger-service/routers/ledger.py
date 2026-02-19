import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from schemas.ledger import LedgerEntryCreate, LedgerEntryResponse, LedgerEntryUpdate, LedgerSummary
from services.customer_service import get_customer
from services.ledger_service import create_ledger_entry, get_ledger_history, update_ledger_entry
from services.security import get_current_user

router = APIRouter(tags=["ledger"])


@router.post("/ledger-entry", response_model=LedgerEntryResponse, status_code=201)
async def create_ledger_entry_endpoint(
    data: LedgerEntryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_ledger_entry(user.id, data, db)


@router.get("/ledger/{customer_id}", response_model=LedgerSummary)
async def get_ledger_history_endpoint(
    customer_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer = await get_customer(customer_id, user.id, db)
    entries, total, total_debit, total_credit, outstanding = await get_ledger_history(
        customer_id, user.id, db, skip=skip, limit=limit
    )
    return LedgerSummary(
        customer_id=customer.id,
        customer_name=customer.name,
        total_debit=str(total_debit),
        total_credit=str(total_credit),
        outstanding_balance=str(outstanding),
        entries=entries,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.put("/ledger-entry/{entry_id}", response_model=LedgerEntryResponse)
async def update_ledger_entry_endpoint(
    entry_id: uuid.UUID,
    data: LedgerEntryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_ledger_entry(entry_id, user.id, data, db)
