from datetime import datetime

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.org import OrgMembership
from schemas.sync import PullResponse, PushRequest, PushResponse, SyncStatusResponse
from services.security import get_org_member, get_write_member
from services.sync_service import get_sync_status, pull_changes, push_changes
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/push", response_model=PushResponse, status_code=201)
async def sync_push(
    body: PushRequest,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    transactions = [t.model_dump() for t in body.transactions]
    ledger_entries = [e.model_dump() for e in body.ledger_entries]

    result = await push_changes(
        db=db,
        user_id=membership.user_id,
        org_id=membership.org_id,
        device_id=body.device_id,
        transactions=transactions,
        ledger_entries=ledger_entries,
    )
    return result


@router.get("/pull", response_model=PullResponse)
async def sync_pull(
    device_id: str = Query(..., min_length=1),
    since: datetime | None = Query(default=None),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    result = await pull_changes(
        db=db,
        user_id=membership.user_id,
        org_id=membership.org_id,
        device_id=device_id,
        since=since,
    )
    return result


@router.get("/status", response_model=SyncStatusResponse)
async def sync_status(
    device_id: str = Query(..., min_length=1),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    result = await get_sync_status(
        db=db,
        user_id=membership.user_id,
        org_id=membership.org_id,
        device_id=device_id,
    )
    return result
