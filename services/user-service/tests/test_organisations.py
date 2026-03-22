import uuid

import pytest
from httpx import AsyncClient
from models.user import User

ORGS_URL = "/organisations"


# ─── Create org ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_org(client: AsyncClient, auth_headers: dict):
    resp = await client.post(ORGS_URL, json={"name": "Acme Corp"}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme Corp"
    assert body["is_personal"] is False
    assert body["is_active"] is True
    assert len(body["members"]) == 1
    assert body["members"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_create_org_requires_auth(client: AsyncClient):
    resp = await client.post(ORGS_URL, json={"name": "No Auth"})
    assert resp.status_code == 401


# ─── List orgs ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_orgs_includes_personal(client: AsyncClient, auth_headers: dict, seed_user: User):
    resp = await client.get(ORGS_URL, headers=auth_headers)
    assert resp.status_code == 200
    orgs = resp.json()
    # seed_user fixture creates a personal org
    assert any(o["is_personal"] is True for o in orgs)
    assert any(o["role"] == "owner" for o in orgs)


@pytest.mark.asyncio
async def test_list_orgs_after_create(client: AsyncClient, auth_headers: dict):
    await client.post(ORGS_URL, json={"name": "New Corp"}, headers=auth_headers)
    resp = await client.get(ORGS_URL, headers=auth_headers)
    assert resp.status_code == 200
    names = [o["name"] for o in resp.json()]
    assert "New Corp" in names


# ─── Get org ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_org(client: AsyncClient, auth_headers: dict):
    create = await client.post(ORGS_URL, json={"name": "Get Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    resp = await client.get(f"{ORGS_URL}/{org_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Corp"


@pytest.mark.asyncio
async def test_get_org_non_member_gets_403(client: AsyncClient, db_session, auth_headers: dict):
    # Create an org owned by a different user
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        password_hash="x",
        full_name="Other",
        phone=None,
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()

    from models.org import Organisation, OrgMembership

    other_org = Organisation(id=uuid.uuid4(), name="Other Corp", owner_id=other_user.id, is_personal=False)
    db_session.add(other_org)
    await db_session.flush()

    other_m = OrgMembership(id=uuid.uuid4(), org_id=other_org.id, user_id=other_user.id, role="owner")
    db_session.add(other_m)
    await db_session.flush()

    resp = await client.get(f"{ORGS_URL}/{other_org.id}", headers=auth_headers)
    assert resp.status_code == 403


# ─── Invite + list members ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_member(client: AsyncClient, auth_headers: dict, db_session):
    # Create a second user to invite
    invitee = User(
        id=uuid.uuid4(),
        email="invitee@example.com",
        password_hash="x",
        full_name="Invitee",
        phone=None,
        is_active=True,
    )
    db_session.add(invitee)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Invite Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    resp = await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "invitee@example.com", "role": "member"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "member"
    assert resp.json()["email"] == "invitee@example.com"


@pytest.mark.asyncio
async def test_invite_duplicate_member_returns_409(client: AsyncClient, auth_headers: dict, db_session):
    invitee = User(
        id=uuid.uuid4(), email="dup@example.com", password_hash="x", full_name="Dup", phone=None, is_active=True
    )
    db_session.add(invitee)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Dup Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    await client.post(
        f"{ORGS_URL}/{org_id}/members", json={"email": "dup@example.com", "role": "member"}, headers=auth_headers
    )
    resp = await client.post(
        f"{ORGS_URL}/{org_id}/members", json={"email": "dup@example.com", "role": "member"}, headers=auth_headers
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, auth_headers: dict, db_session):
    invitee = User(
        id=uuid.uuid4(), email="listmem@example.com", password_hash="x", full_name="ListMem", phone=None, is_active=True
    )
    db_session.add(invitee)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "List Corp"}, headers=auth_headers)
    org_id = create.json()["id"]
    await client.post(
        f"{ORGS_URL}/{org_id}/members", json={"email": "listmem@example.com", "role": "read_only"}, headers=auth_headers
    )

    resp = await client.get(f"{ORGS_URL}/{org_id}/members", headers=auth_headers)
    assert resp.status_code == 200
    emails = [m["email"] for m in resp.json()]
    assert "listmem@example.com" in emails


# ─── Change role ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_change_member_role(client: AsyncClient, auth_headers: dict, db_session, seed_user: User):
    invitee = User(
        id=uuid.uuid4(), email="role@example.com", password_hash="x", full_name="Role", phone=None, is_active=True
    )
    db_session.add(invitee)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Role Corp"}, headers=auth_headers)
    org_id = create.json()["id"]
    await client.post(
        f"{ORGS_URL}/{org_id}/members", json={"email": "role@example.com", "role": "member"}, headers=auth_headers
    )

    resp = await client.patch(
        f"{ORGS_URL}/{org_id}/members/{invitee.id}",
        json={"role": "read_only"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "read_only"


# ─── Remove member ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remove_member(client: AsyncClient, auth_headers: dict, db_session, seed_user: User):
    invitee = User(
        id=uuid.uuid4(), email="remove@example.com", password_hash="x", full_name="Remove", phone=None, is_active=True
    )
    db_session.add(invitee)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Remove Corp"}, headers=auth_headers)
    org_id = create.json()["id"]
    await client.post(
        f"{ORGS_URL}/{org_id}/members", json={"email": "remove@example.com", "role": "member"}, headers=auth_headers
    )

    resp = await client.delete(f"{ORGS_URL}/{org_id}/members/{invitee.id}", headers=auth_headers)
    assert resp.status_code == 204

    # Confirm member is gone from list
    members_resp = await client.get(f"{ORGS_URL}/{org_id}/members", headers=auth_headers)
    emails = [m["email"] for m in members_resp.json()]
    assert "remove@example.com" not in emails


@pytest.mark.asyncio
async def test_cannot_remove_last_owner(client: AsyncClient, auth_headers: dict, seed_user: User):
    create = await client.post(ORGS_URL, json={"name": "Solo Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    resp = await client.delete(f"{ORGS_URL}/{org_id}/members/{seed_user.id}", headers=auth_headers)
    assert resp.status_code == 400
