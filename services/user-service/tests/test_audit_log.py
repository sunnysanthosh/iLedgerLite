"""Tests for audit log endpoint and audit trail creation."""

import uuid

import pytest
from httpx import AsyncClient
from models.user import User

ORGS_URL = "/organisations"


@pytest.fixture
async def org_with_second_user(client: AsyncClient, db_session, auth_headers: dict, seed_user: User):
    """Create an org and invite a second user. Returns (org_id, second_user_id)."""
    # Create a second user directly in DB
    from models.org import Organisation, OrgMembership

    second_user = User(
        id=uuid.uuid4(),
        email="second@audit.example.com",
        password_hash="x",
        full_name="Second User",
        phone=None,
        is_active=True,
    )
    db_session.add(second_user)
    await db_session.flush()

    # Create a non-personal org owned by seed_user
    org = Organisation(
        id=uuid.uuid4(),
        name="Audit Test Org",
        owner_id=seed_user.id,
        is_personal=False,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    membership = OrgMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=seed_user.id,
        role="owner",
        is_active=True,
    )
    db_session.add(membership)
    await db_session.flush()

    return org.id, second_user


async def test_audit_log_requires_auth(client: AsyncClient):
    resp = await client.get(f"{ORGS_URL}/{uuid.uuid4()}/audit")
    assert resp.status_code == 401


async def test_audit_log_after_invite(client: AsyncClient, db_session, auth_headers: dict, seed_user: User):
    """Inviting a member creates an audit entry."""
    from models.org import Organisation, OrgMembership

    # Create org
    org = Organisation(
        id=uuid.uuid4(),
        name="Audit Invite Org",
        owner_id=seed_user.id,
        is_personal=False,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    db_session.add(
        OrgMembership(
            id=uuid.uuid4(),
            org_id=org.id,
            user_id=seed_user.id,
            role="owner",
            is_active=True,
        )
    )
    await db_session.flush()

    # Invite a new user
    invitee = User(
        id=uuid.uuid4(),
        email="invitee@audit.example.com",
        password_hash="x",
        full_name="Invitee",
        phone=None,
        is_active=True,
    )
    db_session.add(invitee)
    await db_session.flush()

    invite_resp = await client.post(
        f"{ORGS_URL}/{org.id}/members",
        json={"email": "invitee@audit.example.com", "role": "member"},
        headers=auth_headers,
    )
    assert invite_resp.status_code == 201

    audit_resp = await client.get(f"{ORGS_URL}/{org.id}/audit", headers=auth_headers)
    assert audit_resp.status_code == 200
    body = audit_resp.json()
    assert body["total"] >= 1
    actions = [e["action"] for e in body["items"]]
    assert "member_invited" in actions


async def test_audit_log_after_role_change(client: AsyncClient, db_session, auth_headers: dict, seed_user: User):
    """Changing a member's role creates an audit entry."""
    from models.org import Organisation, OrgMembership

    org = Organisation(
        id=uuid.uuid4(),
        name="Role Audit Org",
        owner_id=seed_user.id,
        is_personal=False,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    member_user = User(
        id=uuid.uuid4(),
        email="member_role@audit.example.com",
        password_hash="x",
        full_name="Member",
        phone=None,
        is_active=True,
    )
    db_session.add(member_user)
    await db_session.flush()

    db_session.add(OrgMembership(id=uuid.uuid4(), org_id=org.id, user_id=seed_user.id, role="owner", is_active=True))
    db_session.add(OrgMembership(id=uuid.uuid4(), org_id=org.id, user_id=member_user.id, role="member", is_active=True))
    await db_session.flush()

    patch_resp = await client.patch(
        f"{ORGS_URL}/{org.id}/members/{member_user.id}",
        json={"role": "read_only"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200

    audit_resp = await client.get(f"{ORGS_URL}/{org.id}/audit", headers=auth_headers)
    assert audit_resp.status_code == 200
    actions = [e["action"] for e in audit_resp.json()["items"]]
    assert "role_changed" in actions


async def test_audit_log_forbidden_for_non_owner(client: AsyncClient, db_session, seed_user: User):
    """Non-owners cannot view the audit log."""
    from datetime import datetime, timezone

    from config import settings
    from jose import jwt as josejwt
    from models.org import Organisation, OrgMembership

    org = Organisation(
        id=uuid.uuid4(),
        name="Forbidden Audit Org",
        owner_id=seed_user.id,
        is_personal=False,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    member = User(
        id=uuid.uuid4(),
        email="forbidden_audit@example.com",
        password_hash="x",
        full_name="Member",
        phone=None,
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()

    db_session.add(OrgMembership(id=uuid.uuid4(), org_id=org.id, user_id=seed_user.id, role="owner", is_active=True))
    db_session.add(OrgMembership(id=uuid.uuid4(), org_id=org.id, user_id=member.id, role="member", is_active=True))
    await db_session.flush()

    payload = {
        "sub": str(member.id),
        "type": "access",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = josejwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    resp = await client.get(
        f"{ORGS_URL}/{org.id}/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
