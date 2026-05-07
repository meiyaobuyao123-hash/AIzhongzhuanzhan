"""Email sender. Uses SMTP if configured; otherwise logs the link.

For v0.2 simplicity we use stdlib `smtplib` (sync, run in threadpool). v0.3 may
move to aiosmtplib if volume warrants.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.logging_config import logger


async def send_email(to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
    """Send an email. Returns True if SMTP delivery succeeded; False if logged-only fallback.

    Never raises (caller doesn't want auth flow to fail because of email outage).
    """
    if not settings.smtp_host or not settings.smtp_user:
        logger.info(
            "email_fallback_log_only",
            to=to,
            subject=subject,
            body_preview=body_text[:200],
        )
        return False

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
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_send_failed", to=to, error=str(exc))
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
    link = f"{settings.frontend_base}/console/verify-email?token={token}"
    subject, text, html = _build_verification_email(to, link)
    return await send_email(to, subject, text, html)


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
