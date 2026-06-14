"""Tests for the internal /email/send endpoint and email_service rendering."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# /email/send endpoint
# ---------------------------------------------------------------------------


async def test_send_welcome_email_smtp_disabled(client: AsyncClient):
    """When smtp_host is empty (default in tests) the endpoint succeeds silently."""
    resp = await client.post(
        "/email/send",
        json={
            "to_email": "priya@example.com",
            "to_name": "Priya Sharma",
            "template": "welcome",
            "context": {"full_name": "Priya Sharma"},
        },
    )
    assert resp.status_code == 204


async def test_send_invite_email_smtp_disabled(client: AsyncClient):
    """Invite template also succeeds silently when SMTP is not configured."""
    resp = await client.post(
        "/email/send",
        json={
            "to_email": "rajesh@example.com",
            "to_name": "Rajesh Kumar",
            "template": "invite",
            "context": {
                "full_name": "Rajesh Kumar",
                "org_name": "Acme Corp",
                "role": "member",
                "inviter_name": "Priya Sharma",
            },
        },
    )
    assert resp.status_code == 204


async def test_send_email_invalid_template(client: AsyncClient):
    """Unknown template is rejected by Pydantic validation before hitting service."""
    resp = await client.post(
        "/email/send",
        json={
            "to_email": "test@example.com",
            "to_name": "Test",
            "template": "sms",  # not in Literal["welcome", "invite"]
            "context": {},
        },
    )
    assert resp.status_code == 422


async def test_send_email_invalid_address(client: AsyncClient):
    """Malformed email address fails Pydantic EmailStr validation."""
    resp = await client.post(
        "/email/send",
        json={
            "to_email": "not-an-email",
            "to_name": "Bad Address",
            "template": "welcome",
            "context": {},
        },
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("template", ["welcome", "invite"])
async def test_send_email_calls_aiosmtplib_when_enabled(client: AsyncClient, monkeypatch, template):
    """When smtp_host is set aiosmtplib.send is called exactly once."""
    monkeypatch.setattr("config.settings.smtp_host", "smtp.sendgrid.net")

    context = (
        {"full_name": "Priya Sharma"}
        if template == "welcome"
        else {
            "full_name": "Rajesh Kumar",
            "org_name": "Acme Corp",
            "role": "accountant",
            "inviter_name": "Priya Sharma",
        }
    )

    with patch("services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        resp = await client.post(
            "/email/send",
            json={"to_email": "user@example.com", "to_name": "User", "template": template, "context": context},
        )

    assert resp.status_code == 204
    mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Template rendering (unit — no HTTP)
# ---------------------------------------------------------------------------


def test_render_welcome_contains_name():
    from services.email_service import _render

    subject, text, html = _render("welcome", {"full_name": "Anita Patel"})
    assert "Anita Patel" in text
    assert "Anita Patel" in html
    assert "Welcome" in subject


def test_render_invite_contains_org_and_role():
    from services.email_service import _render

    subject, text, html = _render(
        "invite",
        {"full_name": "Vikram Singh", "org_name": "Kumar Textiles", "role": "staff", "inviter_name": "Rajesh Kumar"},
    )
    assert "Kumar Textiles" in text
    assert "staff" in text
    assert "Rajesh Kumar" in text
    assert "Kumar Textiles" in subject


def test_render_unknown_template_raises():
    from services.email_service import _render

    with pytest.raises(ValueError, match="Unknown email template"):
        _render("sms", {})
