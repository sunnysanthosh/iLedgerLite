"""
Smoke Tests — verify all services are up and basic endpoints respond.

Runs in-process using ASGI test clients with SQLite + seed data.
Run with: cd C:/Temp/LedgerLite && pytest tests/smoke/ -v
"""

import pytest

from shared.test_data import USERS, RAW_PASSWORD


# ===========================================================================
# Health Checks
# ===========================================================================
class TestHealthChecks:

    async def test_auth_health(self, seeded_auth_client):
        resp = await seeded_auth_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "auth"

    async def test_user_health(self, seeded_user_client):
        resp = await seeded_user_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "user"

    async def test_txn_health(self, seeded_txn_client):
        resp = await seeded_txn_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "transaction"

    async def test_ledger_health(self, seeded_ledger_client):
        resp = await seeded_ledger_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ledger"


# ===========================================================================
# Auth Service Smoke
# ===========================================================================
class TestAuthSmoke:

    async def test_login_active_user(self, seeded_auth_client):
        """Login with a seeded active user (Priya)."""
        resp = await seeded_auth_client.post(
            "/auth/login",
            json={"email": "priya.sharma@example.com", "password": RAW_PASSWORD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_inactive_user_rejected(self, seeded_auth_client):
        """Inactive user (Meena) should not be able to login."""
        resp = await seeded_auth_client.post(
            "/auth/login",
            json={"email": "meena.reddy@example.com", "password": RAW_PASSWORD},
        )
        assert resp.status_code in (401, 403)

    async def test_login_wrong_password(self, seeded_auth_client):
        """Wrong password returns 401."""
        resp = await seeded_auth_client.post(
            "/auth/login",
            json={"email": "priya.sharma@example.com", "password": "WrongPass@1"},
        )
        assert resp.status_code == 401


# ===========================================================================
# User Service Smoke
# ===========================================================================
class TestUserSmoke:

    async def test_get_profile(self, seeded_user_client, priya_headers):
        """Authenticated user can fetch their profile."""
        resp = await seeded_user_client.get("/users/me", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "priya.sharma@example.com"
        assert data["full_name"] == "Priya Sharma"

    async def test_get_profile_with_settings(self, seeded_user_client, priya_headers):
        """Profile includes embedded settings."""
        resp = await seeded_user_client.get("/users/me", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("settings") is not None


# ===========================================================================
# Transaction Service Smoke
# ===========================================================================
class TestTransactionSmoke:

    async def test_list_accounts(self, seeded_txn_client, priya_headers):
        """User can list their accounts."""
        resp = await seeded_txn_client.get("/accounts", headers=priya_headers)
        assert resp.status_code == 200

    async def test_list_transactions(self, seeded_txn_client, priya_headers):
        """User can list their transactions."""
        resp = await seeded_txn_client.get("/transactions", headers=priya_headers)
        assert resp.status_code == 200

    async def test_list_categories(self, seeded_txn_client, priya_headers):
        """User can list categories."""
        resp = await seeded_txn_client.get("/categories", headers=priya_headers)
        assert resp.status_code == 200


# ===========================================================================
# Ledger Service Smoke
# ===========================================================================
class TestLedgerSmoke:

    async def test_list_customers(self, seeded_ledger_client, rajesh_headers):
        """Business user can list their customers."""
        resp = await seeded_ledger_client.get("/customers", headers=rajesh_headers)
        assert resp.status_code == 200
