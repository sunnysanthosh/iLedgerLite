import time
import uuid

import pytest
from httpx import AsyncClient

from config import settings
from tests.conftest import make_access_token

ME_URL = "/users/me"
ONBOARDING_URL = "/users/me/onboarding"
SETTINGS_URL = "/users/me/settings"


# ─── Health ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "user"}


# ─── Get Profile ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_success(client: AsyncClient, auth_headers: dict):
    resp = await client.get(ME_URL, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "testuser@example.com"
    assert body["full_name"] == "Test User"
    assert body["is_active"] is True
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_get_profile_no_token(client: AsyncClient):
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient):
    resp = await client.get(ME_URL, headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_expired_token(client: AsyncClient):
    from jose import jwt

    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "exp": int(time.time()) - 10,
        "iat": int(time.time()) - 100,
        "jti": "expired-jti",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_nonexistent_user(client: AsyncClient):
    token = make_access_token(str(uuid.uuid4()))
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ─── Update Profile ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_profile_name(client: AsyncClient, auth_headers: dict):
    resp = await client.put(ME_URL, json={"full_name": "Updated Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_profile_phone(client: AsyncClient, auth_headers: dict):
    resp = await client.put(ME_URL, json={"phone": "+919876543210"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+919876543210"


@pytest.mark.asyncio
async def test_update_profile_email_conflict(client: AsyncClient, auth_headers: dict, db_session):
    from models.user import User

    other = User(
        id=uuid.uuid4(),
        email="taken@example.com",
        password_hash="x",
        full_name="Other",
    )
    db_session.add(other)
    await db_session.flush()

    resp = await client.put(ME_URL, json={"email": "taken@example.com"}, headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_profile_no_auth(client: AsyncClient):
    resp = await client.put(ME_URL, json={"full_name": "Hacker"})
    assert resp.status_code == 401


# ─── Onboarding ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_onboarding_success(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        ONBOARDING_URL,
        json={"account_type": "business", "currency": "USD", "language": "hi", "business_category": "retail"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["settings"] is not None
    assert body["settings"]["account_type"] == "business"
    assert body["settings"]["currency"] == "USD"
    assert body["settings"]["language"] == "hi"
    assert body["settings"]["business_category"] == "retail"
    assert body["settings"]["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_onboarding_duplicate(client: AsyncClient, auth_headers: dict):
    await client.post(
        ONBOARDING_URL,
        json={"account_type": "personal"},
        headers=auth_headers,
    )
    resp = await client.post(
        ONBOARDING_URL,
        json={"account_type": "business"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_onboarding_invalid_account_type(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        ONBOARDING_URL,
        json={"account_type": "invalid"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_onboarding_invalid_currency(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        ONBOARDING_URL,
        json={"currency": "TOOLONG"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ─── Settings ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_settings_success(client: AsyncClient, auth_headers: dict):
    resp = await client.put(
        SETTINGS_URL,
        json={"notifications_enabled": False, "language": "ta"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["notifications_enabled"] is False
    assert body["language"] == "ta"


@pytest.mark.asyncio
async def test_update_settings_no_auth(client: AsyncClient):
    resp = await client.put(SETTINGS_URL, json={"language": "en"})
    assert resp.status_code == 401


# ─── Deactivate ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_account(client: AsyncClient, auth_headers: dict):
    resp = await client.delete(ME_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Account deactivated"


@pytest.mark.asyncio
async def test_deactivated_user_cannot_access(client: AsyncClient, seed_user, auth_headers: dict, db_session):
    from sqlalchemy import update

    from models.user import User

    await db_session.execute(update(User).where(User.id == seed_user.id).values(is_active=False))
    await db_session.flush()

    resp = await client.get(ME_URL, headers=auth_headers)
    assert resp.status_code == 401
