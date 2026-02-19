import pytest
from httpx import AsyncClient


ACCOUNTS_URL = "/accounts"


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        ACCOUNTS_URL,
        json={"name": "Savings", "type": "bank", "currency": "INR"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Savings"
    assert body["type"] == "bank"
    assert body["currency"] == "INR"
    assert body["balance"] == "0.00"


@pytest.mark.asyncio
async def test_create_account_invalid_type(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        ACCOUNTS_URL,
        json={"name": "Bad", "type": "invalid_type"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_accounts(client: AsyncClient, auth_headers: dict):
    await client.post(ACCOUNTS_URL, json={"name": "A1", "type": "cash"}, headers=auth_headers)
    resp = await client.get(ACCOUNTS_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(ACCOUNTS_URL, json={"name": "Get Test", "type": "wallet"}, headers=auth_headers)
    aid = create_resp.json()["id"]
    resp = await client.get(f"{ACCOUNTS_URL}/{aid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{ACCOUNTS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(ACCOUNTS_URL, json={"name": "Old Name", "type": "bank"}, headers=auth_headers)
    aid = create_resp.json()["id"]
    resp = await client.put(f"{ACCOUNTS_URL}/{aid}", json={"name": "New Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_deactivate_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(ACCOUNTS_URL, json={"name": "To Delete", "type": "cash"}, headers=auth_headers)
    aid = create_resp.json()["id"]
    resp = await client.delete(f"{ACCOUNTS_URL}/{aid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Account deactivated"


@pytest.mark.asyncio
async def test_accounts_require_auth(client: AsyncClient):
    resp = await client.get(ACCOUNTS_URL)
    assert resp.status_code == 401
