"""Tests for Sync service endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from models.account import Account
from models.customer import Customer

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "sync"


# ---------------------------------------------------------------------------
# Auth required
# ---------------------------------------------------------------------------


async def test_endpoints_require_auth(client: AsyncClient):
    for method, url in [
        ("POST", "/sync/push"),
        ("GET", "/sync/pull?device_id=test"),
        ("GET", "/sync/status?device_id=test"),
    ]:
        resp = await client.request(method, url)
        assert resp.status_code == 401, f"{method} {url} should require auth"


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------


async def test_push_transactions(client: AsyncClient, auth_headers: dict, seed_account: Account):
    txn_id = str(uuid.uuid4())
    resp = await client.post(
        "/sync/push",
        json={
            "device_id": "device-001",
            "transactions": [
                {
                    "id": txn_id,
                    "account_id": str(seed_account.id),
                    "type": "expense",
                    "amount": "350.00",
                    "description": "Coffee shop",
                    "transaction_date": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "ledger_entries": [],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["synced_transactions"] == 1
    assert data["synced_ledger_entries"] == 0
    assert "sync_id" in data


async def test_push_ledger_entries(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    entry_id = str(uuid.uuid4())
    resp = await client.post(
        "/sync/push",
        json={
            "device_id": "device-001",
            "transactions": [],
            "ledger_entries": [
                {
                    "id": entry_id,
                    "customer_id": str(seed_customer.id),
                    "type": "debit",
                    "amount": "5000.00",
                    "description": "Goods delivered",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["synced_transactions"] == 0
    assert data["synced_ledger_entries"] == 1


async def test_push_mixed(client: AsyncClient, auth_headers: dict, seed_account: Account, seed_customer: Customer):
    resp = await client.post(
        "/sync/push",
        json={
            "device_id": "device-002",
            "transactions": [
                {
                    "id": str(uuid.uuid4()),
                    "account_id": str(seed_account.id),
                    "type": "income",
                    "amount": "25000.00",
                    "description": "Salary",
                    "transaction_date": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "ledger_entries": [
                {
                    "id": str(uuid.uuid4()),
                    "customer_id": str(seed_customer.id),
                    "type": "credit",
                    "amount": "2000.00",
                    "description": "Payment received",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["synced_transactions"] == 1
    assert data["synced_ledger_entries"] == 1


async def test_push_idempotent(client: AsyncClient, auth_headers: dict, seed_account: Account):
    """Pushing the same transaction ID twice should upsert (not fail)."""
    txn_id = str(uuid.uuid4())
    payload = {
        "device_id": "device-001",
        "transactions": [
            {
                "id": txn_id,
                "account_id": str(seed_account.id),
                "type": "expense",
                "amount": "100.00",
                "description": "Original",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "ledger_entries": [],
    }

    resp1 = await client.post("/sync/push", json=payload, headers=auth_headers)
    assert resp1.status_code == 201

    # Push again with updated description
    payload["transactions"][0]["description"] = "Updated"
    resp2 = await client.post("/sync/push", json=payload, headers=auth_headers)
    assert resp2.status_code == 201
    assert resp2.json()["synced_transactions"] == 1


async def test_push_empty_batch(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/sync/push",
        json={"device_id": "device-001", "transactions": [], "ledger_entries": []},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["synced_transactions"] == 0
    assert data["synced_ledger_entries"] == 0


async def test_push_validation_missing_device_id(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/sync/push",
        json={"transactions": [], "ledger_entries": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------


async def test_pull_all(client: AsyncClient, auth_headers: dict, seed_server_transactions):
    resp = await client.get(
        "/sync/pull",
        params={"device_id": "device-001"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transactions"]) == 2
    assert "sync_timestamp" in data


async def test_pull_since_timestamp(client: AsyncClient, auth_headers: dict, seed_server_transactions):
    """Pull only changes after a specific timestamp."""
    # Use a timestamp in the future — should get 0 results
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resp = await client.get(
        "/sync/pull",
        params={"device_id": "device-001", "since": future},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transactions"]) == 0
    assert len(data["ledger_entries"]) == 0


async def test_pull_missing_device_id(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/sync/pull", headers=auth_headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


async def test_status_never_synced(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/sync/status",
        params={"device_id": "never-synced-device"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == "never-synced-device"
    assert data["last_synced_at"] is None
    assert data["sync_status"] == "never"


async def test_status_after_push(client: AsyncClient, auth_headers: dict, seed_account: Account):
    device = "status-test-device"
    # Push something first
    await client.post(
        "/sync/push",
        json={
            "device_id": device,
            "transactions": [
                {
                    "id": str(uuid.uuid4()),
                    "account_id": str(seed_account.id),
                    "type": "expense",
                    "amount": "100.00",
                    "description": "test",
                    "transaction_date": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "ledger_entries": [],
        },
        headers=auth_headers,
    )

    resp = await client.get(
        "/sync/status",
        params={"device_id": device},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == device
    assert data["last_synced_at"] is not None
    assert data["sync_status"] == "completed"


async def test_status_missing_device_id(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/sync/status", headers=auth_headers)
    assert resp.status_code == 422
