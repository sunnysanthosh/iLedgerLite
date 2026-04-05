"""Tests that read_only org members are blocked from mutating endpoints."""

from httpx import AsyncClient
from models.customer import Customer


async def test_read_only_cannot_create_customer(client: AsyncClient, read_only_headers: dict):
    resp = await client.post(
        "/customers",
        json={"name": "Should Fail", "phone": "+910000000099"},
        headers=read_only_headers,
    )
    assert resp.status_code == 403


async def test_read_only_can_list_customers(client: AsyncClient, read_only_headers: dict):
    resp = await client.get("/customers", headers=read_only_headers)
    assert resp.status_code == 200


async def test_read_only_cannot_create_ledger_entry(
    client: AsyncClient, read_only_headers: dict, seed_customer: Customer
):
    resp = await client.post(
        "/ledger-entry",
        json={
            "customer_id": str(seed_customer.id),
            "type": "debit",
            "amount": "500.00",
        },
        headers=read_only_headers,
    )
    assert resp.status_code == 403


async def test_read_only_can_view_ledger(client: AsyncClient, read_only_headers: dict, seed_customer: Customer):
    resp = await client.get(f"/ledger/{seed_customer.id}", headers=read_only_headers)
    assert resp.status_code == 200
