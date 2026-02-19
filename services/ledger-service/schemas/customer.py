import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Customer name cannot be empty")
        return v.strip()


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Customer name cannot be empty")
        return v.strip() if v else v


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    phone: str | None
    email: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime


class CustomerWithBalance(CustomerResponse):
    outstanding_balance: str = "0.00"


class CustomerListResponse(BaseModel):
    items: list[CustomerWithBalance]
    total: int
    skip: int
    limit: int
