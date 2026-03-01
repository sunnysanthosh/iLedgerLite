from datetime import datetime

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.user import User
from schemas.sync import PullResponse, PushRequest, PushResponse, SyncStatusResponse
from services.security import get_current_user
from services.sync_service import get_sync_status, pull_changes, push_changes
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/push", response_model=PushResponse, status_code=201)
async def sync_push(
    body: PushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transactions = [t.model_dump() for t in body.transactions]
    ledger_entries = [e.model_dump() for e in body.ledger_entries]

    result = await push_changes(
        db=db,
        user_id=current_user.id,
        device_id=body.device_id,
        transactions=transactions,
        ledger_entries=ledger_entries,
    )
    return result


@router.get("/pull", response_model=PullResponse)
async def sync_pull(
    device_id: str = Query(..., min_length=1),
    since: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await pull_changes(
        db=db,
        user_id=current_user.id,
        device_id=device_id,
        since=since,
    )
    return result


@router.get("/status", response_model=SyncStatusResponse)
async def sync_status(
    device_id: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_sync_status(
        db=db,
        user_id=current_user.id,
        device_id=device_id,
    )
    return result
