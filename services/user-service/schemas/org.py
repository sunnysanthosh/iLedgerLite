import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr


class OrgCreate(BaseModel):
    name: str


class OrgUpdate(BaseModel):
    name: str


class MemberInvite(BaseModel):
    email: EmailStr
    role: Literal["member", "read_only", "accountant", "staff"]


class MemberRoleUpdate(BaseModel):
    role: Literal["owner", "member", "read_only", "accountant", "staff"]


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    permissions: list[str] = []
    is_active: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_membership(cls, membership, user) -> "MemberResponse":
        import json

        perms = membership.permissions
        if isinstance(perms, str):
            perms = json.loads(perms)
        return cls(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role,
            permissions=perms,
            is_active=membership.is_active,
        )


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_personal: bool
    is_active: bool
    members: list[MemberResponse] = []

    model_config = {"from_attributes": True}


class OrgListItem(BaseModel):
    id: uuid.UUID
    name: str
    is_personal: bool
    is_active: bool
    role: str  # caller's role in this org

    model_config = {"from_attributes": True}
