import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from models.customer import Customer

LEDGER_ENTRY_URL = "/ledger-entry"


@pytest.mark.asyncio
async def test_create_ledger_entry_debit(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "500.00",
            "type": "debit",
            "description": "Goods sold on credit",
            "due_date": str(date.today() + timedelta(days=30)),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "debit"
    assert Decimal(body["amount"]) == Decimal("500.00")
    assert body["is_settled"] is False


@pytest.mark.asyncio
async def test_create_ledger_entry_credit(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "200.00",
            "type": "credit",
            "description": "Payment received",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "credit"
    assert body["due_date"] is None


@pytest.mark.asyncio
async def test_create_ledger_entry_invalid_amount(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "-10.00",
            "type": "debit",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_ledger_entry_invalid_type(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "100.00",
            "type": "invalid",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_ledger_entry_nonexistent_customer(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(uuid.uuid4()),
            "amount": "100.00",
            "type": "debit",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_ledger_history(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    # Create a debit and a credit
    await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "1000.00",
            "type": "debit",
            "description": "Large order",
        },
        headers=auth_headers,
    )
    await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "300.00",
            "type": "credit",
            "description": "Partial payment",
        },
        headers=auth_headers,
    )

    resp = await client.get(f"/ledger/{seed_customer.id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == str(seed_customer.id)
    assert body["customer_name"] == "Test Customer"
    assert body["total"] >= 2
    assert Decimal(body["total_debit"]) > 0
    assert Decimal(body["outstanding_balance"]) == Decimal(body["total_debit"]) - Decimal(body["total_credit"])


@pytest.mark.asyncio
async def test_get_ledger_history_pagination(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.get(f"/ledger/{seed_customer.id}?skip=0&limit=1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 1
    assert len(body["entries"]) <= 1


@pytest.mark.asyncio
async def test_get_ledger_history_nonexistent_customer(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/ledger/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_ledger_entry_mark_settled(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    create_resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "250.00",
            "type": "debit",
            "description": "Small order",
        },
        headers=auth_headers,
    )
    entry_id = create_resp.json()["id"]

    resp = await client.put(
        f"{LEDGER_ENTRY_URL}/{entry_id}",
        json={"is_settled": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_settled"] is True


@pytest.mark.asyncio
async def test_update_ledger_entry_partial_payment(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    create_resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "800.00",
            "type": "debit",
        },
        headers=auth_headers,
    )
    entry_id = create_resp.json()["id"]

    resp = await client.put(
        f"{LEDGER_ENTRY_URL}/{entry_id}",
        json={"amount": "500.00", "description": "Reduced after partial payment"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["amount"]) == Decimal("500.00")


@pytest.mark.asyncio
async def test_update_ledger_entry_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.put(
        f"{LEDGER_ENTRY_URL}/{uuid.uuid4()}",
        json={"is_settled": True},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_settled_entries_excluded_from_outstanding(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    # Create a debit entry and mark it settled
    create_resp = await client.post(
        LEDGER_ENTRY_URL,
        json={
            "customer_id": str(seed_customer.id),
            "amount": "9999.00",
            "type": "debit",
            "description": "Will be settled",
        },
        headers=auth_headers,
    )
    entry_id = create_resp.json()["id"]

    # Get balance before settling
    before = await client.get(f"/ledger/{seed_customer.id}", headers=auth_headers)
    balance_before = Decimal(before.json()["outstanding_balance"])

    # Settle it
    await client.put(
        f"{LEDGER_ENTRY_URL}/{entry_id}",
        json={"is_settled": True},
        headers=auth_headers,
    )

    # Balance should decrease by 9999
    after = await client.get(f"/ledger/{seed_customer.id}", headers=auth_headers)
    balance_after = Decimal(after.json()["outstanding_balance"])
    assert balance_after == balance_before - Decimal("9999.00")


@pytest.mark.asyncio
async def test_ledger_entries_require_auth(client: AsyncClient):
    resp = await client.post(LEDGER_ENTRY_URL, json={"customer_id": str(uuid.uuid4()), "amount": "10", "type": "debit"})
    assert resp.status_code == 401
