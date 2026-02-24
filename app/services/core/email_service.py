"""
Email service for transactional emails (verification, password reset).

When MAIL_ENABLED=False (e.g. APP_ENV=test), all send functions are no-ops
so the test suite never needs a real SMTP connection.
"""

from __future__ import annotations

import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTML email templates
# ---------------------------------------------------------------------------

_VERIFY_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0;">
  <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:8px;padding:40px;">
    <h2 style="color:#2d3748;">Welcome to Bizify 🚀</h2>
    <p style="color:#4a5568;">Thanks for signing up! Please verify your email address to activate your account.</p>
    <a href="{link}"
       style="display:inline-block;margin-top:20px;padding:12px 24px;background:#4f46e5;color:#fff;
              text-decoration:none;border-radius:6px;font-weight:bold;">
      Verify Email
    </a>
    <p style="margin-top:24px;color:#718096;font-size:12px;">
      This link expires in <strong>24 hours</strong>.
      If you didn't create an account, you can safely ignore this email.
    </p>
    <p style="color:#718096;font-size:12px;">
      Or copy this URL into your browser:<br>
      <span style="color:#4f46e5;">{link}</span>
    </p>
  </div>
</body>
</html>
"""

_RESET_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0;">
  <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:8px;padding:40px;">
    <h2 style="color:#2d3748;">Password Reset Request 🔐</h2>
    <p style="color:#4a5568;">We received a request to reset your password. Click the button below to choose a new one.</p>
    <a href="{link}"
       style="display:inline-block;margin-top:20px;padding:12px 24px;background:#e53e3e;color:#fff;
              text-decoration:none;border-radius:6px;font-weight:bold;">
      Reset Password
    </a>
    <p style="margin-top:24px;color:#718096;font-size:12px;">
      This link expires in <strong>15 minutes</strong>.
      If you didn't request a password reset, you can safely ignore this email.
    </p>
    <p style="color:#718096;font-size:12px;">
      Or copy this URL into your browser:<br>
      <span style="color:#e53e3e;">{link}</span>
    </p>
  </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Internal SMTP send helper (lazy-imports fastapi-mail to keep startup fast)
# ---------------------------------------------------------------------------


async def _send(to_email: str, subject: str, html_body: str) -> None:
    """Low-level async sender. Imports fastapi-mail only when needed."""
    from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_TLS,
        MAIL_SSL_TLS=settings.MAIL_SSL,
        USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
        VALIDATE_CERTS=True,
    )

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_verification_email(email: str, token: str) -> None:
    """
    Send an account verification email.

    No-op when ``settings.MAIL_ENABLED`` is False (test / local dev without SMTP).
    """
    if not settings.MAIL_ENABLED:
        logger.info("MAIL_ENABLED=False — skipping verification email to %s", email)
        return

    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html_body = _VERIFY_TEMPLATE.format(link=link)

    try:
        await _send(email, "Verify your Bizify account", html_body)
        logger.info("Verification email sent to %s", email)
    except Exception:
        # Log but never crash the registration flow — user can request a resend
        logger.exception("Failed to send verification email to %s", email)


async def send_password_reset_email(email: str, token: str) -> None:
    """
    Send a password-reset email containing a one-time link.

    No-op when ``settings.MAIL_ENABLED`` is False.
    """
    if not settings.MAIL_ENABLED:
        logger.info("MAIL_ENABLED=False — skipping password reset email to %s", email)
        return

    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html_body = _RESET_TEMPLATE.format(link=link)

    try:
        await _send(email, "Reset your Bizify password", html_body)
        logger.info("Password reset email sent to %s", email)
    except Exception:
        logger.exception("Failed to send password reset email to %s", email)
