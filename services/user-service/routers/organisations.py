import uuid

from db import get_db
from fastapi import APIRouter, Depends, status
from models.user import User
from schemas.org import MemberInvite, MemberResponse, MemberRoleUpdate, OrgCreate, OrgListItem, OrgResponse
from services.org_service import (
    change_member_role,
    create_org,
    get_org,
    invite_member,
    list_members,
    list_orgs,
    remove_member,
)
from services.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/organisations", tags=["organisations"])


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_org(data, current_user, db)


@router.get("", response_model=list[OrgListItem])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_orgs(current_user, db)


@router.get("/{org_id}", response_model=OrgResponse)
async def get_one(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_org(org_id, current_user, db)


@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite(
    org_id: uuid.UUID,
    data: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await invite_member(org_id, data, current_user, db)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def get_members(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_members(org_id, current_user, db)


@router.patch("/{org_id}/members/{target_user_id}", response_model=MemberResponse)
async def update_member_role(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    data: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await change_member_role(org_id, target_user_id, data, current_user, db)


@router.delete("/{org_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_member(org_id, target_user_id, current_user, db)
