import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool
    related_entity_id: uuid.UUID | None
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationResponse]
    total: int
    skip: int
    limit: int
    unread_count: int


class ReminderRequest(BaseModel):
    customer_id: uuid.UUID
    message: str | None = None

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: uuid.UUID) -> uuid.UUID:
        if v is None:
            raise ValueError("customer_id is required")
        return v


class MarkReadResponse(BaseModel):
    id: uuid.UUID
    is_read: bool


class InternalNotificationCreate(BaseModel):
    user_id: uuid.UUID
    org_id: uuid.UUID
    type: str = "system"
    title: str
    message: str
    related_entity_id: uuid.UUID | None = None
