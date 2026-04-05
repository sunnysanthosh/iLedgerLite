import json
import uuid

from fastapi import HTTPException, status
from models.audit_log import AuditLog
from models.org import Organisation, OrgMembership
from models.user import User
from schemas.org import MemberInvite, MemberResponse, MemberRoleUpdate, OrgCreate, OrgListItem, OrgResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def _audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    entry = AuditLog(
        id=uuid.uuid4(),
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    await db.flush()


async def create_org(data: OrgCreate, owner: User, db: AsyncSession) -> OrgResponse:
    org = Organisation(
        id=uuid.uuid4(),
        name=data.name,
        owner_id=owner.id,
        is_personal=False,
        is_active=True,
    )
    db.add(org)
    await db.flush()

    membership = OrgMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=owner.id,
        role="owner",
        is_active=True,
    )
    db.add(membership)
    await db.flush()

    return OrgResponse(
        id=org.id,
        name=org.name,
        is_personal=org.is_personal,
        is_active=org.is_active,
        members=[
            MemberResponse(
                user_id=owner.id,
                email=owner.email,
                full_name=owner.full_name,
                role="owner",
                is_active=True,
            )
        ],
    )


async def list_orgs(user: User, db: AsyncSession) -> list[OrgListItem]:
    result = await db.execute(
        select(OrgMembership)
        .options(selectinload(OrgMembership.organisation))
        .where(OrgMembership.user_id == user.id, OrgMembership.is_active.is_(True))
        .execution_options(populate_existing=True)
    )
    memberships = result.scalars().all()
    return [
        OrgListItem(
            id=m.organisation.id,
            name=m.organisation.name,
            is_personal=m.organisation.is_personal,
            is_active=m.organisation.is_active,
            role=m.role,
        )
        for m in memberships
        if m.organisation.is_active
    ]


async def get_org(org_id: uuid.UUID, user: User, db: AsyncSession) -> OrgResponse:
    membership = await _require_membership(org_id, user.id, db)
    members = await _load_members(org_id, db)
    return OrgResponse(
        id=membership.organisation.id,
        name=membership.organisation.name,
        is_personal=membership.organisation.is_personal,
        is_active=membership.organisation.is_active,
        members=members,
    )


async def invite_member(org_id: uuid.UUID, data: MemberInvite, inviter: User, db: AsyncSession) -> MemberResponse:
    membership = await _require_membership(org_id, inviter.id, db)
    if membership.role not in ("owner", "member"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners and members can invite")

    # Look up invitee by email
    result = await db.execute(select(User).where(User.email == data.email))
    invitee = result.scalars().first()
    if invitee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check not already a member
    existing = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == invitee.id,
        )
    )
    existing_m = existing.scalars().first()
    if existing_m is not None:
        if existing_m.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")
        # Re-activate if previously deactivated
        existing_m.is_active = True
        existing_m.role = data.role
        await db.flush()
        return MemberResponse(
            user_id=invitee.id,
            email=invitee.email,
            full_name=invitee.full_name,
            role=data.role,
            is_active=True,
        )

    new_membership = OrgMembership(
        id=uuid.uuid4(),
        org_id=org_id,
        user_id=invitee.id,
        role=data.role,
        invited_by=inviter.id,
        is_active=True,
    )
    db.add(new_membership)
    await db.flush()

    await _audit(
        db,
        org_id,
        inviter.id,
        "member_invited",
        "org_membership",
        invitee.id,
        {"email": invitee.email, "role": data.role},
    )

    return MemberResponse(
        user_id=invitee.id,
        email=invitee.email,
        full_name=invitee.full_name,
        role=data.role,
        is_active=True,
    )


async def list_members(org_id: uuid.UUID, user: User, db: AsyncSession) -> list[MemberResponse]:
    await _require_membership(org_id, user.id, db)
    return await _load_members(org_id, db)


async def change_member_role(
    org_id: uuid.UUID, target_user_id: uuid.UUID, data: MemberRoleUpdate, requester: User, db: AsyncSession
) -> MemberResponse:
    requester_m = await _require_membership(org_id, requester.id, db)
    if requester_m.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can change roles")

    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id, OrgMembership.user_id == target_user_id, OrgMembership.is_active.is_(True)
        )
    )
    target_m = result.scalars().first()
    if target_m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    old_role = target_m.role
    target_m.role = data.role
    await db.flush()

    result2 = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result2.scalars().first()

    await _audit(
        db,
        org_id,
        requester.id,
        "role_changed",
        "org_membership",
        target_user_id,
        {"from": old_role, "to": data.role, "email": target_user.email},
    )

    return MemberResponse(
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=data.role,
        is_active=True,
    )


async def remove_member(org_id: uuid.UUID, target_user_id: uuid.UUID, requester: User, db: AsyncSession) -> None:
    requester_m = await _require_membership(org_id, requester.id, db)
    if requester_m.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can remove members")

    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id, OrgMembership.user_id == target_user_id, OrgMembership.is_active.is_(True)
        )
    )
    target_m = result.scalars().first()
    if target_m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Cannot remove last owner
    if target_m.role == "owner":
        owners_result = await db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id, OrgMembership.role == "owner", OrgMembership.is_active.is_(True)
            )
        )
        owners = owners_result.scalars().all()
        if len(owners) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last owner of an organisation"
            )

    removed_role = target_m.role
    target_m.is_active = False
    await db.flush()

    result3 = await db.execute(select(User).where(User.id == target_user_id))
    removed_user = result3.scalars().first()
    await _audit(
        db,
        org_id,
        requester.id,
        "member_removed",
        "org_membership",
        target_user_id,
        {"email": removed_user.email if removed_user else None, "role": removed_role},
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _require_membership(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    required_role: str | None = None,
) -> OrgMembership:
    result = await db.execute(
        select(OrgMembership)
        .options(selectinload(OrgMembership.organisation))
        .where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
            OrgMembership.is_active.is_(True),
        )
        .execution_options(populate_existing=True)
    )
    membership = result.scalars().first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organisation")
    if required_role and membership.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Only {required_role}s can perform this action"
        )
    return membership


async def _load_members(org_id: uuid.UUID, db: AsyncSession) -> list[MemberResponse]:
    result = await db.execute(
        select(OrgMembership, User)
        .join(User, OrgMembership.user_id == User.id)
        .where(OrgMembership.org_id == org_id, OrgMembership.is_active.is_(True))
    )
    rows = result.all()
    return [
        MemberResponse(
            user_id=m.user_id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            is_active=m.is_active,
        )
        for m, u in rows
    ]


async def list_audit_log(
    org_id: uuid.UUID,
    user: User,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list, int]:
    """Return audit log entries for the org. Owners only."""
    await _require_membership(org_id, user.id, db, required_role="owner")

    from sqlalchemy import func as sqlfunc

    count_result = await db.execute(select(sqlfunc.count()).select_from(AuditLog).where(AuditLog.org_id == org_id))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.org_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .execution_options(populate_existing=True)
    )
    entries = result.scalars().all()
    return entries, total
