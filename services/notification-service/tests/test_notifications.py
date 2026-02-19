"""Notification service tests using shared seed data.

Primary test user: Rajesh (USER_RAJESH_ID) — has customers with ledger entries.
"""
import uuid

import pytest

from shared.test_data import (
    CUST_SURESH_TEXTILES_ID,
    USER_RAJESH_ID,
    rajesh_headers,
    priya_headers,
)


# ──── Health ────

async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "notification"


# ──── Auth required ────

async def test_endpoints_require_auth(client):
    endpoints = [
        ("GET", "/notifications"),
        ("PUT", f"/notifications/{uuid.uuid4()}/read"),
        ("POST", "/notifications/reminder"),
    ]
    for method, url in endpoints:
        kwargs = {"json": {}} if method == "POST" else {}
        resp = await getattr(client, method.lower())(url, **kwargs)
        assert resp.status_code in (401, 422), f"{method} {url} should require auth"


# ──── List notifications ────

async def test_list_notifications(client, seed_notifications):
    headers = rajesh_headers()
    resp = await client.get("/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["unread_count"] == 2
    assert len(data["items"]) == 3


async def test_list_notifications_unread_only(client, seed_notifications):
    headers = rajesh_headers()
    resp = await client.get("/notifications?unread_only=true", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(not item["is_read"] for item in data["items"])


async def test_list_notifications_pagination(client, seed_notifications):
    headers = rajesh_headers()
    resp = await client.get("/notifications?skip=0&limit=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


async def test_list_notifications_empty(client, seed_full_data):
    """Priya has no notifications — seed_full_data loaded but no notifs for her."""
    headers = priya_headers()
    resp = await client.get("/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert len(data["items"]) == 0


# ──── Mark as read ────

async def test_mark_as_read(client, seed_notifications):
    unread = [n for n in seed_notifications if not n.is_read][0]
    headers = rajesh_headers()
    resp = await client.put(f"/notifications/{unread.id}/read", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_read"] is True


async def test_mark_as_read_not_found(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.put(f"/notifications/{uuid.uuid4()}/read", headers=headers)
    assert resp.status_code == 404


# ──── Reminder ────

async def test_create_reminder(client, seed_full_data):
    """Suresh Textiles has outstanding balance of 23000."""
    headers = rajesh_headers()
    resp = await client.post(
        "/notifications/reminder",
        json={"customer_id": CUST_SURESH_TEXTILES_ID},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "reminder"
    assert "Suresh Textiles" in data["title"]
    assert data["is_read"] is False
    assert data["related_entity_id"] == CUST_SURESH_TEXTILES_ID


async def test_create_reminder_custom_message(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.post(
        "/notifications/reminder",
        json={
            "customer_id": CUST_SURESH_TEXTILES_ID,
            "message": "Please pay your dues ASAP",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["message"] == "Please pay your dues ASAP"


async def test_create_reminder_customer_not_found(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.post(
        "/notifications/reminder",
        json={"customer_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_create_reminder_no_outstanding_balance(client, seed_customer_no_balance):
    """Customer with no ledger entries should fail."""
    headers = rajesh_headers()
    resp = await client.post(
        "/notifications/reminder",
        json={"customer_id": str(seed_customer_no_balance.id)},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "no outstanding balance" in resp.json()["detail"].lower()
