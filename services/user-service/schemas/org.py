import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr


class OrgCreate(BaseModel):
    name: str


class OrgUpdate(BaseModel):
    name: str


class MemberInvite(BaseModel):
    email: EmailStr
    role: Literal["member", "read_only"]


class MemberRoleUpdate(BaseModel):
    role: Literal["owner", "member", "read_only"]


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


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
