import asyncio
import json
import logging
import uuid

import httpx
from config import settings
from fastapi import HTTPException, status
from models.audit_log import AuditLog
from models.org import Organisation, OrgMembership
from models.user import User
from schemas.org import MemberInvite, MemberResponse, MemberRoleUpdate, OrgCreate, OrgListItem, OrgResponse
from services.permissions import resolve_permissions
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


async def _notify_invite(
    invitee_id: uuid.UUID,
    org_id: uuid.UUID,
    org_name: str,
    role: str,
    invitee_email: str,
    invitee_name: str,
    inviter_name: str,
) -> None:
    """Fire-and-forget: in-app system notification + transactional invite email."""
    async with httpx.AsyncClient(timeout=3.0) as client:
        # In-app notification
        try:
            await client.post(
                f"{settings.notification_service_url}/notifications/internal",
                json={
                    "user_id": str(invitee_id),
                    "org_id": str(org_id),
                    "type": "system",
                    "title": f"You've been invited to {org_name}",
                    "message": f"You have been added to '{org_name}' with role '{role}'.",
                    "related_entity_id": str(org_id),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not send invite notification: %s", exc)

        # Invite email
        try:
            await client.post(
                f"{settings.notification_service_url}/email/send",
                json={
                    "to_email": invitee_email,
                    "to_name": invitee_name,
                    "template": "invite",
                    "context": {
                        "full_name": invitee_name,
                        "org_name": org_name,
                        "role": role,
                        "inviter_name": inviter_name,
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not send invite email: %s", exc)


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
        existing_m.permissions = json.dumps(resolve_permissions(data.role))
        await db.flush()
        return MemberResponse.from_membership(existing_m, invitee)

    new_membership = OrgMembership(
        id=uuid.uuid4(),
        org_id=org_id,
        user_id=invitee.id,
        role=data.role,
        permissions=json.dumps(resolve_permissions(data.role)),
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

    asyncio.create_task(
        _notify_invite(
            invitee.id,
            org_id,
            membership.organisation.name,
            data.role,
            invitee.email,
            invitee.full_name,
            inviter.full_name,
        )
    )

    return MemberResponse.from_membership(new_membership, invitee)


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
    target_m.permissions = json.dumps(resolve_permissions(data.role))
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

    return MemberResponse.from_membership(target_m, target_user)


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
    return [MemberResponse.from_membership(m, u) for m, u in result.all()]


async def delete_org(org_id: uuid.UUID, user: User, db: AsyncSession) -> None:
    """Soft-delete an org. Blocked for personal orgs and orgs with other active members."""
    membership = await _require_membership(org_id, user.id, db, required_role="owner")
    org = membership.organisation

    if org.is_personal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Personal organisations cannot be deleted")

    other_members = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id != user.id,
            OrgMembership.is_active.is_(True),
        )
    )
    if other_members.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remove all other members before deleting the organisation",
        )

    org.is_active = False
    membership.is_active = False
    await db.flush()
    await _audit(db, org_id, user.id, "org_deleted", "organisation", org_id, {"name": org.name})


async def transfer_org(org_id: uuid.UUID, to_user_id: uuid.UUID, requester: User, db: AsyncSession) -> MemberResponse:
    """Transfer ownership to another active member."""
    await _require_membership(org_id, requester.id, db, required_role="owner")

    result = await db.execute(
        select(OrgMembership, User)
        .join(User, OrgMembership.user_id == User.id)
        .where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == to_user_id,
            OrgMembership.is_active.is_(True),
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not an active member")

    target_m, target_user = row

    # Downgrade current owner → member
    requester_result = await db.execute(
        select(OrgMembership).where(OrgMembership.org_id == org_id, OrgMembership.user_id == requester.id)
    )
    requester_m = requester_result.scalars().first()
    requester_m.role = "member"
    requester_m.permissions = json.dumps(resolve_permissions("member"))

    # Upgrade target → owner
    target_m.role = "owner"
    target_m.permissions = json.dumps(resolve_permissions("owner"))

    # Update org owner_id
    org_result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = org_result.scalars().first()
    org.owner_id = to_user_id

    await db.flush()
    await _audit(
        db,
        org_id,
        requester.id,
        "ownership_transferred",
        "organisation",
        org_id,
        {"from_user": str(requester.id), "to_user": str(to_user_id), "to_email": target_user.email},
    )

    return MemberResponse.from_membership(target_m, target_user)


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
