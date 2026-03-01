import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

VALID_CATEGORY_TYPES = {"income", "expense"}


class CategoryCreate(BaseModel):
    name: str
    type: str
    icon: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_CATEGORY_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_CATEGORY_TYPES))}")
        return v


class CategoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    type: str
    icon: str | None
    is_system: bool
    created_at: datetime

    model_config = {"from_attributes": True}
