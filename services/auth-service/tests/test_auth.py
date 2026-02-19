import time

import pytest
from httpx import AsyncClient

from services.security import create_access_token, create_refresh_token

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"
REFRESH_URL = "/auth/refresh"

VALID_USER = {
    "email": "test@example.com",
    "password": "securepass123",
    "full_name": "Test User",
    "phone": "+911234567890",
}


# ─── Health ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "auth"}


# ─── Register ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["full_name"] == VALID_USER["full_name"]
    assert "id" in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    data = {**VALID_USER, "email": "weak@example.com", "password": "short"}
    resp = await client.post(REGISTER_URL, json=data)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json={"email": "x@x.com"})
    assert resp.status_code == 422


# ─── Login ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(REGISTER_URL, json={**VALID_USER, "email": "login@example.com"})
    resp = await client.post(LOGIN_URL, json={"email": "login@example.com", "password": VALID_USER["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(REGISTER_URL, json={**VALID_USER, "email": "wrong@example.com"})
    resp = await client.post(LOGIN_URL, json={"email": "wrong@example.com", "password": "badpassword1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    resp = await client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "anything1234"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session):
    from sqlalchemy import select, update

    from models.user import User

    await client.post(REGISTER_URL, json={**VALID_USER, "email": "inactive@example.com"})
    await db_session.execute(update(User).where(User.email == "inactive@example.com").values(is_active=False))
    await db_session.flush()

    resp = await client.post(LOGIN_URL, json={"email": "inactive@example.com", "password": VALID_USER["password"]})
    assert resp.status_code == 401


# ─── Me (profile) ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_valid_token(client: AsyncClient):
    await client.post(REGISTER_URL, json={**VALID_USER, "email": "me@example.com"})
    login = await client.post(LOGIN_URL, json={"email": "me@example.com", "password": VALID_USER["password"]})
    token = login.json()["access_token"]

    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_missing_token(client: AsyncClient):
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_expired_token(client: AsyncClient):
    from config import settings
    from jose import jwt

    payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "type": "access",
        "exp": int(time.time()) - 10,
        "iat": int(time.time()) - 100,
        "jti": "expired-jti",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ─── Refresh ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient):
    await client.post(REGISTER_URL, json={**VALID_USER, "email": "refresh@example.com"})
    login = await client.post(LOGIN_URL, json={"email": "refresh@example.com", "password": VALID_USER["password"]})
    refresh_token = login.json()["refresh_token"]

    resp = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["refresh_token"] != refresh_token  # rotated


@pytest.mark.asyncio
async def test_refresh_token_reuse(client: AsyncClient):
    await client.post(REGISTER_URL, json={**VALID_USER, "email": "reuse@example.com"})
    login = await client.post(LOGIN_URL, json={"email": "reuse@example.com", "password": VALID_USER["password"]})
    refresh_token = login.json()["refresh_token"]

    # First use succeeds
    resp1 = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp1.status_code == 200

    # Second use of same token fails (single-use rotation)
    resp2 = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post(REFRESH_URL, json={"refresh_token": "not.a.real.token"})
    assert resp.status_code == 401
