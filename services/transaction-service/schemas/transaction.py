import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

VALID_TRANSACTION_TYPES = {"income", "expense", "transfer"}


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    type: str
    amount: Decimal
    description: str | None = None
    transaction_date: datetime

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TRANSACTION_TYPES))}")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransactionUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    type: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    transaction_date: datetime | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TRANSACTION_TYPES))}")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    type: str
    amount: Decimal
    description: str | None
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    skip: int
    limit: int
