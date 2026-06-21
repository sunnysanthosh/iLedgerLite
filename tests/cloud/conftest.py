"""
Cloud verification suite — fixtures for hitting a REAL deployed environment.

Unlike tests/smoke and tests/regression (in-process ASGI clients + SQLite),
this suite makes real HTTP requests over the public internet to a deployed
staging stack: real ingress (nginx), real TLS (cert-manager), real Cloud SQL.

Run only against a live environment (`make test-cloud` after `Staging — Start`).
Never run as part of `make test-e2e` or in PR CI.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient

CLOUD_TEST_EMAIL = "cloud-verify@ledgerlite.internal"
CLOUD_TEST_FULL_NAME = "Cloud Verify"


def base_url() -> str:
    return os.environ.get("CLOUD_BASE_URL", "https://api.staging.ledgerlite.app").rstrip("/") + "/api"


def test_password() -> str:
    # Falls back to a fixed default for manual local runs against a throwaway
    # staging account. Set CLOUD_TEST_PASSWORD in CI (cloud-verify.yml).
    return os.environ.get("CLOUD_TEST_PASSWORD", "CloudVerify@2026")


@pytest.fixture(scope="session")
async def cloud_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url=base_url(), timeout=15.0) as client:
        yield client


@pytest.fixture(scope="session")
async def auth_token(cloud_client: AsyncClient) -> str:
    """Idempotent login-or-register against the deployed auth-service via ingress."""
    password = test_password()

    login_resp = await cloud_client.post(
        "/auth/login",
        json={"email": CLOUD_TEST_EMAIL, "password": password},
    )
    if login_resp.status_code == 200:
        return login_resp.json()["access_token"]

    register_resp = await cloud_client.post(
        "/auth/register",
        json={
            "email": CLOUD_TEST_EMAIL,
            "password": password,
            "full_name": CLOUD_TEST_FULL_NAME,
        },
    )
    assert register_resp.status_code in (201, 409), (
        f"Unexpected register response: {register_resp.status_code} {register_resp.text}"
    )

    login_resp = await cloud_client.post(
        "/auth/login",
        json={"email": CLOUD_TEST_EMAIL, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed after register: {login_resp.status_code} {login_resp.text}"
    return login_resp.json()["access_token"]


@pytest.fixture(scope="session")
async def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}
