"""Tests that read_only org members are blocked from mutating endpoints."""

import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from models.account import Account


async def test_read_only_cannot_create_transaction(client: AsyncClient, read_only_headers: dict, seed_account: Account):
    resp = await client.post(
        "/transactions",
        json={
            "account_id": str(seed_account.id),
            "type": "expense",
            "amount": "100.00",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=read_only_headers,
    )
    assert resp.status_code == 403


async def test_read_only_can_list_transactions(client: AsyncClient, read_only_headers: dict):
    resp = await client.get("/transactions", headers=read_only_headers)
    assert resp.status_code == 200


async def test_read_only_cannot_create_account(client: AsyncClient, read_only_headers: dict):
    resp = await client.post(
        "/accounts",
        json={"name": "Bad Account", "type": "cash", "currency": "INR"},
        headers=read_only_headers,
    )
    assert resp.status_code == 403


async def test_read_only_can_list_accounts(client: AsyncClient, read_only_headers: dict):
    resp = await client.get("/accounts", headers=read_only_headers)
    assert resp.status_code == 200


async def test_read_only_cannot_delete_transaction(client: AsyncClient, read_only_headers: dict):
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/transactions/{fake_id}", headers=read_only_headers)
    # 403 before even hitting the DB lookup
    assert resp.status_code == 403
