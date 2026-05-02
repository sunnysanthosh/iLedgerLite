import logging
from email.message import EmailMessage

import aiosmtplib
from config import settings

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    return bool(settings.smtp_host)


def _render(template: str, context: dict) -> tuple[str, str, str]:
    """Return (subject, plain_text, html). Raises ValueError for unknown template."""
    if template == "welcome":
        name = context.get("full_name", "there")
        subject = "Welcome to iLedger!"
        text = (
            f"Hi {name},\n\n"
            "Welcome to iLedger. Your account is ready to use.\n\n"
            "Get started at https://app.iledger.app\n\n"
            "— The iLedger Team"
        )
        html = f"""<p>Hi {name},</p>
<p>Welcome to <strong>iLedger</strong>. Your account is all set up and ready to use.</p>
<p><a href="https://app.iledger.app">Open iLedger &rarr;</a></p>
<p>&mdash; The iLedger Team</p>"""

    elif template == "invite":
        name = context.get("full_name", "there")
        org_name = context.get("org_name", "an organisation")
        inviter_name = context.get("inviter_name", "Someone")
        role = context.get("role", "member")
        subject = f"You've been invited to {org_name} on iLedger"
        text = (
            f"Hi {name},\n\n"
            f"{inviter_name} has invited you to join '{org_name}' as {role} on iLedger.\n\n"
            "Open iLedger at https://app.iledger.app to get started.\n\n"
            "— The iLedger Team"
        )
        html = f"""<p>Hi {name},</p>
<p><strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong>
as <em>{role}</em> on iLedger.</p>
<p><a href="https://app.iledger.app">Accept &amp; Open iLedger &rarr;</a></p>
<p>&mdash; The iLedger Team</p>"""

    else:
        raise ValueError(f"Unknown email template: {template!r}")

    return subject, text, html


async def send_email(to_email: str, to_name: str, template: str, context: dict) -> None:
    """Send a templated transactional email via SMTP. No-op when smtp_host is not configured."""
    if not is_enabled():
        logger.debug("Email disabled (SMTP_HOST not set) — skipping %s to %s", template, to_email)
        return

    subject, text, html = _render(template, context)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"iLedger <{settings.smtp_from}>"
    msg["To"] = f"{to_name} <{to_email}>"
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    # Port 465 = implicit TLS; port 587 = STARTTLS (default for SendGrid)
    use_tls = settings.smtp_port == 465
    start_tls = settings.smtp_port != 465

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        logger.info("Email sent: template=%s to=%s", template, to_email)
    except Exception as exc:
        logger.error("SMTP send failed: template=%s to=%s error=%s", template, to_email, exc)
        raise
