# ruff: noqa
"""
Email service for transactional emails (verification, password reset).

When MAIL_ENABLED=False (e.g. APP_ENV=test), all send functions are no-ops
so the test suite never needs a real SMTP connection.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from config.settings import settings
from app.core.events import dispatcher

logger = logging.getLogger(__name__)

import os
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "email")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

from app.services.base_service import BaseService
from sqlalchemy.ext.asyncio import AsyncSession

class EmailService(BaseService):
    """Service for sending transactional emails."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    def render_template(self, template_name: str, **context) -> str:
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

    async def _queue_email(self, to_email: str, subject: str, html_body: str) -> None:
        """Add email to the database queue for asynchronous processing."""
        from app.db.database import AsyncSessionLocal
        from app.models.core.core import EmailMessage

        async with AsyncSessionLocal() as db:
            try:
                msg = EmailMessage(
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                    status="PENDING"
                )
                db.add(msg)
                await db.commit()
                logger.info("Email queued for %s (subject: %s)", to_email, subject)
            except Exception as e:
                await db.rollback()
                logger.error("Failed to queue email for %s: %s", to_email, e)

    async def send_verification_email(self, email: str, token: str) -> None:
        """Queue an account verification email using HTML template."""
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        html_body = self.render_template(
            "base.html",
            title="Verify Email",
            heading="Welcome to Bizify 🚀",
            content_html="Thanks for signing up! Please verify your email address to activate your account.",
            button_url=link,
            button_text="Verify Email",
            footer_text="This link expires in 24 hours. If you didn't create an account, you can safely ignore this.",
            fallback_url=link
        )
        await self._queue_email(email, "Verify your Bizify account", html_body)

    async def send_password_reset_email(self, email: str, token: str) -> None:
        """Queue a password-reset email using HTML template."""
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        html_body = self.render_template(
            "base.html",
            title="Password Reset",
            heading="Password Reset Request 🔐",
            content_html="We received a request to reset your password. Click the button below to choose a new one.",
            button_url=link,
            button_text="Reset Password",
            footer_text="This link expires in 15 minutes. If you didn't request a reset, you can safely ignore this.",
            fallback_url=link
        )
        await self._queue_email(email, "Reset your Bizify password", html_body)

    @staticmethod
    async def handle_auth_event(event_type: str, payload: Dict[str, Any]):
        """Async handler for authentication events."""
        email = payload.get("email")
        token = payload.get("token")
        if not email or not token:
            return

        service = EmailService()
        if event_type == "auth.user_registered":
            await service.send_verification_email(email, token)
        elif event_type == "auth.password_reset_requested":
            await service.send_password_reset_email(email, token)

def register_email_handlers():
    """Register EmailService handlers with the dispatcher."""
    dispatcher.subscribe("auth.user_registered", EmailService.handle_auth_event)
    dispatcher.subscribe("auth.password_reset_requested", EmailService.handle_auth_event)

# ---------------------------------------------------------------------------
# Public API (Legacy Aliases)
# ---------------------------------------------------------------------------

async def send_verification_email(email: str, token: str) -> None:
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await EmailService(db).send_verification_email(email, token)

async def send_password_reset_email(email: str, token: str) -> None:
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await EmailService(db).send_password_reset_email(email, token)
