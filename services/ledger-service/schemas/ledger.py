import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class LedgerEntryCreate(BaseModel):
    customer_id: uuid.UUID
    amount: Decimal
    type: str
    due_date: date | None = None
    description: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("debit", "credit"):
            raise ValueError("Type must be 'debit' or 'credit'")
        return v


class LedgerEntryUpdate(BaseModel):
    amount: Decimal | None = None
    type: str | None = None
    description: str | None = None
    due_date: date | None = None
    is_settled: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("debit", "credit"):
            raise ValueError("Type must be 'debit' or 'credit'")
        return v


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    customer_id: uuid.UUID
    type: str
    amount: str
    description: str | None
    due_date: date | None
    is_settled: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("amount", mode="before")
    @classmethod
    def amount_to_string(cls, v: Decimal | str) -> str:
        return str(v)


class LedgerSummary(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    total_debit: str = "0.00"
    total_credit: str = "0.00"
    outstanding_balance: str = "0.00"
    entries: list[LedgerEntryResponse]
    total: int
    skip: int
    limit: int
