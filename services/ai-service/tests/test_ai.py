"""Tests for AI service endpoints."""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "ai"


# ---------------------------------------------------------------------------
# Auth required
# ---------------------------------------------------------------------------

async def test_endpoints_require_auth(client: AsyncClient):
    for method, url in [
        ("POST", "/ai/categorize"),
        ("GET", "/ai/insights"),
        ("POST", "/ai/ocr"),
    ]:
        resp = await client.request(method, url)
        assert resp.status_code == 401, f"{method} {url} should require auth"


# ---------------------------------------------------------------------------
# Categorize
# ---------------------------------------------------------------------------

async def test_categorize_groceries(client: AsyncClient, auth_headers: dict, seed_categories):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "Weekly grocery shopping at BigBasket", "amount": "1500.00", "type": "expense"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictions"]) > 0
    # Groceries should be top prediction due to keyword match
    assert data["predictions"][0]["category_name"] == "Groceries"
    assert data["predictions"][0]["confidence"] > 0.3


async def test_categorize_transport(client: AsyncClient, auth_headers: dict, seed_categories):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "Uber ride to office", "amount": "250.00", "type": "expense"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["predictions"][0]["category_name"] == "Transport"


async def test_categorize_salary_income(client: AsyncClient, auth_headers: dict, seed_categories):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "Monthly salary deposit", "amount": "50000.00", "type": "income"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["predictions"][0]["category_name"] == "Salary"


async def test_categorize_no_keyword_match(client: AsyncClient, auth_headers: dict, seed_categories):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "Random payment XYZ", "amount": "100.00", "type": "expense"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should return fallback suggestions
    assert len(data["predictions"]) > 0


async def test_categorize_validation_empty_description(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "", "amount": "100.00", "type": "expense"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_categorize_validation_invalid_type(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/ai/categorize",
        json={"description": "test", "amount": "100.00", "type": "transfer"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_categorize_has_category_id(client: AsyncClient, auth_headers: dict, seed_categories):
    """Predictions for known categories should include the DB category_id."""
    resp = await client.post(
        "/ai/categorize",
        json={"description": "Swiggy dinner order", "amount": "450.00", "type": "expense"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    top = resp.json()["predictions"][0]
    assert top["category_name"] == "Food & Dining"
    assert top["category_id"] is not None


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

async def test_insights_with_data(client: AsyncClient, auth_headers: dict, seed_transactions):
    resp = await client.get("/ai/insights", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "anomalies" in data
    assert "trends" in data
    assert "top_categories" in data
    assert "total_income_30d" in data
    assert "total_expense_30d" in data
    # We seeded 50000 income in last 30 days
    assert float(data["total_income_30d"]) == 50000.0
    # We seeded 2500+800+1200 = 4500 expense in last 30 days
    assert float(data["total_expense_30d"]) == 4500.0


async def test_insights_trends(client: AsyncClient, auth_headers: dict, seed_transactions):
    resp = await client.get("/ai/insights", headers=auth_headers)
    data = resp.json()
    # Groceries: 2500 vs 1000 → increasing (>50% deviation = anomaly)
    grocery_trend = next((t for t in data["trends"] if t["category_name"] == "Groceries"), None)
    assert grocery_trend is not None
    assert grocery_trend["trend"] == "increasing"


async def test_insights_anomalies(client: AsyncClient, auth_headers: dict, seed_transactions):
    resp = await client.get("/ai/insights", headers=auth_headers)
    data = resp.json()
    # Groceries jumped from 1000 to 2500 (150% increase) — should be flagged
    grocery_anomaly = next((a for a in data["anomalies"] if a["category_name"] == "Groceries"), None)
    assert grocery_anomaly is not None
    assert grocery_anomaly["deviation"] > 0.5


async def test_insights_empty(client: AsyncClient, auth_headers: dict, seed_categories):
    """User with no transactions should get empty insights."""
    resp = await client.get("/ai/insights", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["anomalies"] == []
    assert data["trends"] == []
    assert float(data["total_income_30d"]) == 0
    assert float(data["total_expense_30d"]) == 0


# ---------------------------------------------------------------------------
# OCR (mock)
# ---------------------------------------------------------------------------

async def test_ocr_mock(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/ai/ocr",
        json={"image_base64": "iVBORw0KGgo=", "filename": "receipt.jpg"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["merchant"] == "Star Bazaar Supermarket"
    assert data["amount"] == "1249.00"
    assert len(data["items"]) == 4
    assert data["confidence"] == 0.85


async def test_ocr_no_filename(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/ai/ocr",
        json={"image_base64": "abc123"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["merchant"] == "Star Bazaar Supermarket"


async def test_ocr_empty_image(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/ai/ocr",
        json={"image_base64": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422
