import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    details: str | None
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogEntry]
    total: int
    skip: int
    limit: int
