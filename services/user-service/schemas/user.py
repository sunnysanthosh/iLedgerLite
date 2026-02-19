import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: "UserSettingsResponse | None" = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class OnboardingRequest(BaseModel):
    account_type: str = "personal"
    currency: str = "INR"
    language: str = "en"
    business_category: str | None = None

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        allowed = {"personal", "business", "both"}
        if v not in allowed:
            raise ValueError(f"account_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class SettingsUpdate(BaseModel):
    notifications_enabled: bool | None = None
    language: str | None = None
    currency: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Currency must be a 3-letter ISO code")
            return v.upper()
        return v


class UserSettingsResponse(BaseModel):
    account_type: str
    currency: str
    language: str
    business_category: str | None
    notifications_enabled: bool
    onboarding_completed: bool

    model_config = {"from_attributes": True}


# Rebuild UserProfile now that UserSettingsResponse is defined
UserProfile.model_rebuild()
