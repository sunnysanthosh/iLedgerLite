import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

VALID_ACCOUNT_TYPES = {"cash", "bank", "credit_card", "wallet", "loan"}


class AccountCreate(BaseModel):
    name: str
    type: str
    currency: str = "INR"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_ACCOUNT_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_ACCOUNT_TYPES))}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class AccountUpdate(BaseModel):
    name: str | None = None
    type: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ACCOUNT_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_ACCOUNT_TYPES))}")
        return v


class AccountResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
