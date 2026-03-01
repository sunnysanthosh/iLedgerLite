import uuid

import pytest
from httpx import AsyncClient
from models.customer import Customer

CUSTOMERS_URL = "/customers"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "ledger"}


@pytest.mark.asyncio
async def test_create_customer(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        CUSTOMERS_URL,
        json={
            "name": "Ravi Kumar",
            "phone": "+919876500001",
            "email": "ravi@example.com",
            "address": "456 Market Road",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ravi Kumar"
    assert body["phone"] == "+919876500001"
    assert body["email"] == "ravi@example.com"


@pytest.mark.asyncio
async def test_create_customer_name_only(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        CUSTOMERS_URL,
        json={"name": "Simple Customer"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Simple Customer"
    assert body["phone"] is None


@pytest.mark.asyncio
async def test_create_customer_empty_name(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        CUSTOMERS_URL,
        json={"name": "  "},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_customers(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.get(CUSTOMERS_URL, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1
    assert "outstanding_balance" in body["items"][0]


@pytest.mark.asyncio
async def test_list_customers_search(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.get(f"{CUSTOMERS_URL}?search=Test", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert "test" in item["name"].lower() or "test" in (item["email"] or "").lower()


@pytest.mark.asyncio
async def test_list_customers_search_no_results(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{CUSTOMERS_URL}?search=nonexistent_xyz", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_customers_pagination(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{CUSTOMERS_URL}?skip=0&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 2
    assert len(body["items"]) <= 2


@pytest.mark.asyncio
async def test_get_customer(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.get(f"{CUSTOMERS_URL}/{seed_customer.id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Test Customer"
    assert "outstanding_balance" in body


@pytest.mark.asyncio
async def test_get_customer_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{CUSTOMERS_URL}/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_customer(client: AsyncClient, auth_headers: dict, seed_customer: Customer):
    resp = await client.put(
        f"{CUSTOMERS_URL}/{seed_customer.id}",
        json={"name": "Updated Name", "phone": "+919876500099"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Updated Name"
    assert body["phone"] == "+919876500099"


@pytest.mark.asyncio
async def test_update_customer_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.put(
        f"{CUSTOMERS_URL}/{uuid.uuid4()}",
        json={"name": "No One"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_customers_require_auth(client: AsyncClient):
    resp = await client.get(CUSTOMERS_URL)
    assert resp.status_code == 401
