import pytest
from httpx import AsyncClient

CATEGORIES_URL = "/categories"


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        CATEGORIES_URL,
        json={"name": "Groceries", "type": "expense", "icon": "cart"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Groceries"
    assert body["type"] == "expense"
    assert body["icon"] == "cart"
    assert body["is_system"] is False


@pytest.mark.asyncio
async def test_create_category_invalid_type(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        CATEGORIES_URL,
        json={"name": "Bad", "type": "invalid"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, auth_headers: dict):
    await client.post(CATEGORIES_URL, json={"name": "Salary", "type": "income"}, headers=auth_headers)
    await client.post(CATEGORIES_URL, json={"name": "Rent", "type": "expense"}, headers=auth_headers)
    resp = await client.get(CATEGORIES_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_list_categories_filter_by_type(client: AsyncClient, auth_headers: dict):
    await client.post(CATEGORIES_URL, json={"name": "Bonus", "type": "income"}, headers=auth_headers)
    resp = await client.get(f"{CATEGORIES_URL}?type=income", headers=auth_headers)
    assert resp.status_code == 200
    for cat in resp.json():
        assert cat["type"] == "income"


@pytest.mark.asyncio
async def test_categories_require_auth(client: AsyncClient):
    resp = await client.get(CATEGORIES_URL)
    assert resp.status_code == 401
