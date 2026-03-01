import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from models.account import Account

TXN_URL = "/transactions"
ACCOUNTS_URL = "/accounts"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "transaction"}


@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient, auth_headers: dict, seed_account: Account):
    resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "income",
            "amount": "500.00",
            "description": "Freelance payment",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "income"
    assert Decimal(body["amount"]) == Decimal("500.00")
    assert body["description"] == "Freelance payment"


@pytest.mark.asyncio
async def test_create_transaction_updates_balance(client: AsyncClient, auth_headers: dict, seed_account: Account):
    await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "200.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    acct = await client.get(f"{ACCOUNTS_URL}/{seed_account.id}", headers=auth_headers)
    assert Decimal(acct.json()["balance"]) == Decimal("800.00")


@pytest.mark.asyncio
async def test_create_transaction_invalid_amount(client: AsyncClient, auth_headers: dict, seed_account: Account):
    resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "-10.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_invalid_type(client: AsyncClient, auth_headers: dict, seed_account: Account):
    resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "invalid",
            "amount": "10.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_nonexistent_account(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(uuid.uuid4()),
            "type": "income",
            "amount": "100.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient, auth_headers: dict, seed_account: Account):
    for i in range(3):
        await client.post(
            TXN_URL,
            json={
                "account_id": str(seed_account.id),
                "type": "expense",
                "amount": "10.00",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
    resp = await client.get(TXN_URL, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 3
    assert len(body["items"]) >= 3


@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(client: AsyncClient, auth_headers: dict, seed_account: Account):
    await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "income",
            "amount": "99.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    resp = await client.get(f"{TXN_URL}?type=income", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["type"] == "income"


@pytest.mark.asyncio
async def test_list_transactions_pagination(client: AsyncClient, auth_headers: dict, seed_account: Account):
    resp = await client.get(f"{TXN_URL}?skip=0&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 2
    assert len(body["items"]) <= 2


@pytest.mark.asyncio
async def test_get_transaction(client: AsyncClient, auth_headers: dict, seed_account: Account):
    create_resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "42.00",
            "description": "Coffee",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    txn_id = create_resp.json()["id"]
    resp = await client.get(f"{TXN_URL}/{txn_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Coffee"


@pytest.mark.asyncio
async def test_get_transaction_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{TXN_URL}/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient, auth_headers: dict, seed_account: Account):
    create_resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "50.00",
            "description": "Lunch",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    txn_id = create_resp.json()["id"]
    resp = await client.put(
        f"{TXN_URL}/{txn_id}",
        json={"amount": "75.00", "description": "Dinner"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["amount"]) == Decimal("75.00")
    assert resp.json()["description"] == "Dinner"


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient, auth_headers: dict, seed_account: Account):
    create_resp = await client.post(
        TXN_URL,
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "30.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_headers,
    )
    txn_id = create_resp.json()["id"]
    resp = await client.delete(f"{TXN_URL}/{txn_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Transaction deleted"

    # Verify it's gone
    get_resp = await client.get(f"{TXN_URL}/{txn_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_transactions_require_auth(client: AsyncClient):
    resp = await client.get(TXN_URL)
    assert resp.status_code == 401
