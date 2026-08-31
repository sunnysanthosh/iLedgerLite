import uuid

import pytest
from httpx import AsyncClient
from models.user import User

from shared.test_data import make_access_token

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


# ─── Delete org ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_org(client: AsyncClient, auth_headers: dict):
    """Owner can delete an org that has no other members."""
    create = await client.post(ORGS_URL, json={"name": "Delete Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    resp = await client.delete(f"{ORGS_URL}/{org_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Deleted org no longer appears in list
    list_resp = await client.get(ORGS_URL, headers=auth_headers)
    names = [o["name"] for o in list_resp.json()]
    assert "Delete Corp" not in names


@pytest.mark.asyncio
async def test_delete_personal_org_blocked(client: AsyncClient, auth_headers: dict, seed_user: User):
    """Personal org cannot be deleted."""
    # Get the personal org id from list
    list_resp = await client.get(ORGS_URL, headers=auth_headers)
    personal = next(o for o in list_resp.json() if o["is_personal"])

    resp = await client.delete(f"{ORGS_URL}/{personal['id']}", headers=auth_headers)
    assert resp.status_code == 400
    assert "personal" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_org_with_members_blocked(client: AsyncClient, auth_headers: dict, db_session):
    """Cannot delete an org that still has other active members."""
    other = User(
        id=uuid.uuid4(),
        email="del_member@example.com",
        password_hash="x",
        full_name="DelMember",
        phone=None,
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Busy Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "del_member@example.com", "role": "member"},
        headers=auth_headers,
    )

    resp = await client.delete(f"{ORGS_URL}/{org_id}", headers=auth_headers)
    assert resp.status_code == 400
    assert "member" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_org_non_member_blocked(client: AsyncClient, auth_headers: dict, db_session):
    """Non-member cannot delete an org."""
    other = User(
        id=uuid.uuid4(),
        email="stranger@example.com",
        password_hash="x",
        full_name="Stranger",
        phone=None,
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    from models.org import Organisation, OrgMembership

    other_org = Organisation(
        id=uuid.uuid4(), name="Stranger Corp", owner_id=other.id, is_personal=False, is_active=True
    )
    db_session.add(other_org)
    await db_session.flush()

    other_m = OrgMembership(id=uuid.uuid4(), org_id=other_org.id, user_id=other.id, role="owner", is_active=True)
    db_session.add(other_m)
    await db_session.flush()

    resp = await client.delete(f"{ORGS_URL}/{other_org.id}", headers=auth_headers)
    assert resp.status_code == 403


# ─── Transfer org ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transfer_org(client: AsyncClient, auth_headers: dict, db_session):
    """Owner can transfer ownership to an existing member."""
    new_owner = User(
        id=uuid.uuid4(),
        email="newowner@example.com",
        password_hash="x",
        full_name="New Owner",
        phone=None,
        is_active=True,
    )
    db_session.add(new_owner)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Transfer Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "newowner@example.com", "role": "member"},
        headers=auth_headers,
    )

    resp = await client.post(
        f"{ORGS_URL}/{org_id}/transfer",
        json={"to_user_id": str(new_owner.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "newowner@example.com"
    assert body["role"] == "owner"


@pytest.mark.asyncio
async def test_transfer_old_owner_becomes_member(client: AsyncClient, auth_headers: dict, db_session, seed_user: User):
    """After transfer the original owner's role is downgraded to member."""
    new_owner = User(
        id=uuid.uuid4(),
        email="takeover@example.com",
        password_hash="x",
        full_name="Takeover",
        phone=None,
        is_active=True,
    )
    db_session.add(new_owner)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Handoff Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "takeover@example.com", "role": "member"},
        headers=auth_headers,
    )

    await client.post(
        f"{ORGS_URL}/{org_id}/transfer",
        json={"to_user_id": str(new_owner.id)},
        headers=auth_headers,
    )

    members_resp = await client.get(f"{ORGS_URL}/{org_id}/members", headers=auth_headers)
    members = {m["email"]: m["role"] for m in members_resp.json()}
    assert members[seed_user.email] == "member"
    assert members["takeover@example.com"] == "owner"


@pytest.mark.asyncio
async def test_transfer_to_non_member_blocked(client: AsyncClient, auth_headers: dict, db_session):
    """Cannot transfer to a user who is not an active member."""
    outsider = User(
        id=uuid.uuid4(),
        email="outsider@example.com",
        password_hash="x",
        full_name="Outsider",
        phone=None,
        is_active=True,
    )
    db_session.add(outsider)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "No Transfer Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    resp = await client.post(
        f"{ORGS_URL}/{org_id}/transfer",
        json={"to_user_id": str(outsider.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_transfer_requires_owner(client: AsyncClient, auth_headers: dict, db_session):
    """A non-owner member cannot initiate a transfer."""
    member_user = User(
        id=uuid.uuid4(),
        email="justmember@example.com",
        password_hash="x",
        full_name="JustMember",
        phone=None,
        is_active=True,
    )
    other_target = User(
        id=uuid.uuid4(), email="target@example.com", password_hash="x", full_name="Target", phone=None, is_active=True
    )
    db_session.add(member_user)
    db_session.add(other_target)
    await db_session.flush()

    create = await client.post(ORGS_URL, json={"name": "Guard Corp"}, headers=auth_headers)
    org_id = create.json()["id"]

    await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "justmember@example.com", "role": "member"},
        headers=auth_headers,
    )
    await client.post(
        f"{ORGS_URL}/{org_id}/members",
        json={"email": "target@example.com", "role": "member"},
        headers=auth_headers,
    )

    member_headers = {"Authorization": f"Bearer {make_access_token(str(member_user.id))}"}
    resp = await client.post(
        f"{ORGS_URL}/{org_id}/transfer",
        json={"to_user_id": str(other_target.id)},
        headers=member_headers,
    )
    assert resp.status_code == 403
