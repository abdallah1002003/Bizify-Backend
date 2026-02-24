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

import os
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "email")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

def render_template(template_name: str, **context) -> str:
    """Helper to render a Jinja2 template."""
    try:
        # Inject global branding context
        context.setdefault("app_name", settings.APP_NAME)
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception:
        logger.exception("Failed to render template %s", template_name)
        # Fallback to a very basic string if template rendering fails
        return f"<html><body>{context.get('content_html', '')}</body></html>"

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
    Send an account verification email using HTML template.
    """
    if not settings.MAIL_ENABLED:
        logger.info("MAIL_ENABLED=False — skipping verification email to %s", email)
        return

    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html_body = render_template(
        "base.html",
        title="Verify Email",
        heading="Welcome to Bizify 🚀",
        content_html="Thanks for signing up! Please verify your email address to activate your account.",
        button_url=link,
        button_text="Verify Email",
        footer_text="This link expires in 24 hours. If you didn't create an account, you can safely ignore this.",
        fallback_url=link
    )

    try:
        await _send(email, "Verify your Bizify account", html_body)
        logger.info("Verification email sent to %s", email)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)


async def send_password_reset_email(email: str, token: str) -> None:
    """
    Send a password-reset email using HTML template.
    """
    if not settings.MAIL_ENABLED:
        logger.info("MAIL_ENABLED=False — skipping password reset email to %s", email)
        return

    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html_body = render_template(
        "base.html",
        title="Password Reset",
        heading="Password Reset Request 🔐",
        content_html="We received a request to reset your password. Click the button below to choose a new one.",
        button_url=link,
        button_text="Reset Password",
        footer_text="This link expires in 15 minutes. If you didn't request a reset, you can safely ignore this.",
        fallback_url=link
    )

    try:
        await _send(email, "Reset your Bizify password", html_body)
        logger.info("Password reset email sent to %s", email)
    except Exception:
        logger.exception("Failed to send password reset email to %s", email)
