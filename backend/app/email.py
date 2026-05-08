"""Email sender. Tries Resend HTTP API first, then SMTP, finally logs to journal.

Provider priority:
  1. Resend (settings.resend_api_key set) — POST https://api.resend.com/emails
  2. SMTP (settings.smtp_host + settings.smtp_user set) — stdlib smtplib STARTTLS
  3. Fallback: structlog the link so admin can pull it from journal
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import httpx

from app.config import settings
from app.logging_config import logger


async def _send_via_resend(
    to: str, subject: str, body_text: str, body_html: str | None,
) -> bool:
    """POST to Resend's REST API. Docs: https://resend.com/docs/api-reference/emails/send-email"""
    payload: dict = {
        "from": settings.smtp_from,
        "to": [to],
        "subject": subject,
        "text": body_text,
    }
    if body_html:
        payload["html"] = body_html

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code in (200, 201, 202):
            logger.info(
                "email_sent_via_resend",
                to=to, subject=subject,
                resend_id=resp.json().get("id"),
            )
            return True
        logger.error(
            "email_resend_failed",
            to=to, status=resp.status_code, body=resp.text[:300],
        )
        return False
    except Exception as exc:
        logger.error("email_resend_exception", to=to, error=str(exc))
        return False


async def _send_via_smtp(
    to: str, subject: str, body_text: str, body_html: str | None,
) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    def _smtp_send_sync():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

    try:
        await asyncio.to_thread(_smtp_send_sync)
        logger.info("email_sent_via_smtp", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_smtp_failed", to=to, error=str(exc))
        return False


async def send_email(
    to: str, subject: str, body_text: str, body_html: str | None = None,
) -> bool:
    """Send an email via Resend → SMTP → fallback log. Never raises."""
    if settings.resend_api_key:
        return await _send_via_resend(to, subject, body_text, body_html)
    if settings.smtp_host and settings.smtp_user:
        return await _send_via_smtp(to, subject, body_text, body_html)
    logger.info(
        "email_fallback_log_only",
        to=to, subject=subject, body_preview=body_text[:200],
    )
    return False


def _build_verification_email(to: str, link: str) -> tuple[str, str, str]:
    subject = "Welcome to Prism — verify your email"
    text = (
        f"Welcome to Prism!\n\n"
        f"Click the link below within 24 hours to verify your email address:\n\n"
        f"  {link}\n\n"
        f"If you didn't sign up for Prism, ignore this email.\n\n"
        f"— Prism · cost = price · always"
    )
    html = (
        f"<p>Welcome to Prism!</p>"
        f"<p>Click the link below within 24 hours to verify your email address:</p>"
        f"<p><a href=\"{link}\">{link}</a></p>"
        f"<p>If you didn't sign up for Prism, ignore this email.</p>"
        f"<p style=\"color:#888\">— Prism · cost = price · always</p>"
    )
    return subject, text, html


async def send_verification_email(to: str, token: str) -> bool:
    link = f"{settings.frontend_base}/verify-email?token={token}"
    subject, text, html = _build_verification_email(to, link)
    return await send_email(to, subject, text, html)


def email_provider_status() -> dict:
    """Diagnostic snapshot — what provider would `send_email` use right now?"""
    if settings.resend_api_key:
        return {"provider": "resend", "configured": True,
                "from": settings.smtp_from}
    if settings.smtp_host and settings.smtp_user:
        return {"provider": "smtp", "configured": True,
                "host": settings.smtp_host, "port": settings.smtp_port,
                "user": settings.smtp_user, "from": settings.smtp_from}
    return {"provider": "log_only", "configured": False,
            "hint": "Set PRISM_RESEND_API_KEY (recommended) or PRISM_SMTP_HOST + PRISM_SMTP_USER + PRISM_SMTP_PASSWORD"}


async def send_password_reset_email(to: str, token: str) -> bool:
    link = f"{settings.frontend_base}/reset-password?token={token}"
    subject = "Prism — reset your password"
    text = (
        f"You requested a password reset. Click the link below within 1 hour:\n\n"
        f"  {link}\n\n"
        f"If you didn't request this, ignore this email."
    )
    html = (
        f"<p>You requested a password reset. Click the link below within 1 hour:</p>"
        f"<p><a href=\"{link}\">{link}</a></p>"
        f"<p>If you didn't request this, ignore this email.</p>"
    )
    return await send_email(to, subject, text, html)
