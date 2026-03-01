import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

# --- Push ---


class TransactionPush(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    type: str = Field(..., pattern="^(income|expense|transfer)$")
    amount: Decimal = Field(..., gt=0)
    description: str | None = None
    transaction_date: datetime


class LedgerEntryPush(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    type: str = Field(..., pattern="^(debit|credit)$")
    amount: Decimal = Field(..., gt=0)
    description: str | None = None
    due_date: date | None = None
    is_settled: bool = False


class PushRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    transactions: list[TransactionPush] = []
    ledger_entries: list[LedgerEntryPush] = []


class PushResponse(BaseModel):
    synced_transactions: int
    synced_ledger_entries: int
    sync_id: uuid.UUID


# --- Pull ---


class TransactionPull(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    type: str
    amount: str
    description: str | None
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("amount", mode="before")
    @classmethod
    def amount_to_str(cls, v):
        return str(v)


class LedgerEntryPull(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    type: str
    amount: str
    description: str | None
    due_date: date | None
    is_settled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("amount", mode="before")
    @classmethod
    def amount_to_str(cls, v):
        return str(v)


class PullResponse(BaseModel):
    transactions: list[TransactionPull]
    ledger_entries: list[LedgerEntryPull]
    sync_timestamp: datetime


# --- Status ---


class SyncStatusResponse(BaseModel):
    device_id: str
    last_synced_at: datetime | None
    sync_status: str
    pending_transactions: int
    pending_ledger_entries: int
