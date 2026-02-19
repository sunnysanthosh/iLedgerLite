"""Sync service: push/pull changes, track sync status."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ledger_entry import LedgerEntry
from models.sync_log import SyncLog
from models.transaction import Transaction


async def push_changes(
    db: AsyncSession,
    user_id: uuid.UUID,
    device_id: str,
    transactions: list[dict],
    ledger_entries: list[dict],
) -> dict:
    """Accept local changes from a device (last-write-wins on conflict)."""
    synced_txn = 0
    synced_ledger = 0

    # Upsert transactions (last-write-wins: if ID exists, overwrite)
    for txn_data in transactions:
        existing = await db.execute(
            select(Transaction).where(
                Transaction.id == txn_data["id"],
                Transaction.user_id == user_id,
            )
        )
        existing_txn = existing.scalars().first()
        if existing_txn:
            existing_txn.account_id = txn_data["account_id"]
            existing_txn.category_id = txn_data.get("category_id")
            existing_txn.type = txn_data["type"]
            existing_txn.amount = txn_data["amount"]
            existing_txn.description = txn_data.get("description")
            existing_txn.transaction_date = txn_data["transaction_date"]
        else:
            new_txn = Transaction(
                id=txn_data["id"],
                user_id=user_id,
                account_id=txn_data["account_id"],
                category_id=txn_data.get("category_id"),
                type=txn_data["type"],
                amount=txn_data["amount"],
                description=txn_data.get("description"),
                transaction_date=txn_data["transaction_date"],
            )
            db.add(new_txn)
        synced_txn += 1

    # Upsert ledger entries
    for entry_data in ledger_entries:
        existing = await db.execute(
            select(LedgerEntry).where(
                LedgerEntry.id == entry_data["id"],
                LedgerEntry.user_id == user_id,
            )
        )
        existing_entry = existing.scalars().first()
        if existing_entry:
            existing_entry.customer_id = entry_data["customer_id"]
            existing_entry.type = entry_data["type"]
            existing_entry.amount = entry_data["amount"]
            existing_entry.description = entry_data.get("description")
            existing_entry.due_date = entry_data.get("due_date")
            existing_entry.is_settled = entry_data.get("is_settled", False)
        else:
            new_entry = LedgerEntry(
                id=entry_data["id"],
                user_id=user_id,
                customer_id=entry_data["customer_id"],
                type=entry_data["type"],
                amount=entry_data["amount"],
                description=entry_data.get("description"),
                due_date=entry_data.get("due_date"),
                is_settled=entry_data.get("is_settled", False),
            )
            db.add(new_entry)
        synced_ledger += 1

    await db.flush()

    # Record sync log
    sync_log = SyncLog(
        id=uuid.uuid4(),
        user_id=user_id,
        device_id=device_id,
        last_synced_at=datetime.now(timezone.utc),
        sync_status="completed",
        changes_pushed=synced_txn + synced_ledger,
        changes_pulled=0,
    )
    db.add(sync_log)
    await db.flush()

    return {
        "synced_transactions": synced_txn,
        "synced_ledger_entries": synced_ledger,
        "sync_id": sync_log.id,
    }


async def pull_changes(
    db: AsyncSession,
    user_id: uuid.UUID,
    device_id: str,
    since: datetime | None,
) -> dict:
    """Return server changes since the given timestamp."""
    # Transactions modified since last sync
    txn_query = select(Transaction).where(Transaction.user_id == user_id)
    if since:
        txn_query = txn_query.where(Transaction.updated_at > since)
    txn_query = txn_query.order_by(Transaction.updated_at)

    txn_result = await db.execute(txn_query)
    transactions = txn_result.scalars().all()

    # Ledger entries modified since last sync
    entry_query = select(LedgerEntry).where(LedgerEntry.user_id == user_id)
    if since:
        entry_query = entry_query.where(LedgerEntry.updated_at > since)
    entry_query = entry_query.order_by(LedgerEntry.updated_at)

    entry_result = await db.execute(entry_query)
    ledger_entries = entry_result.scalars().all()

    now = datetime.now(timezone.utc)

    # Record sync log
    sync_log = SyncLog(
        id=uuid.uuid4(),
        user_id=user_id,
        device_id=device_id,
        last_synced_at=now,
        sync_status="completed",
        changes_pushed=0,
        changes_pulled=len(transactions) + len(ledger_entries),
    )
    db.add(sync_log)
    await db.flush()

    return {
        "transactions": transactions,
        "ledger_entries": ledger_entries,
        "sync_timestamp": now,
    }


async def get_sync_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    device_id: str,
) -> dict:
    """Return last sync info and count of pending changes for this device."""
    # Find the most recent sync for this device
    result = await db.execute(
        select(SyncLog)
        .where(SyncLog.user_id == user_id, SyncLog.device_id == device_id)
        .order_by(SyncLog.last_synced_at.desc())
        .limit(1)
    )
    last_sync = result.scalars().first()

    last_synced_at = last_sync.last_synced_at if last_sync else None
    sync_status = last_sync.sync_status if last_sync else "never"

    # Count changes since last sync
    pending_txn = 0
    pending_ledger = 0
    if last_synced_at:
        txn_count = await db.execute(
            select(func.count()).select_from(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.updated_at > last_synced_at,
            )
        )
        pending_txn = txn_count.scalar() or 0

        entry_count = await db.execute(
            select(func.count()).select_from(LedgerEntry).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.updated_at > last_synced_at,
            )
        )
        pending_ledger = entry_count.scalar() or 0

    return {
        "device_id": device_id,
        "last_synced_at": last_synced_at,
        "sync_status": sync_status,
        "pending_transactions": pending_txn,
        "pending_ledger_entries": pending_ledger,
    }
