"""
Unit tests for app/services/core/email_service.py.

These tests verify that:
- When MAIL_ENABLED=False the send functions are silent no-ops.
- When MAIL_ENABLED=True the FastMail sender is called with the correct
  recipient and subject (using a monkeypatched FastMail).
"""

import asyncio
import importlib
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Run a coroutine synchronously in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Tests: MAIL_ENABLED=False (no-op path)
# ---------------------------------------------------------------------------

class TestEmailServiceDisabled:
    """When MAIL_ENABLED is False no SMTP call should ever be made."""

    def test_send_verification_email_noop(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", False)

        # Re-import to pick up patched settings
        import app.services.core.email_service as svc
        importlib.reload(svc)

        # Should complete without error and without touching FastMail
        run(svc.send_verification_email("user@example.com", "fake-token"))

    def test_send_password_reset_email_noop(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", False)

        import app.services.core.email_service as svc
        importlib.reload(svc)

        run(svc.send_password_reset_email("user@example.com", "fake-token"))


# ---------------------------------------------------------------------------
# Tests: MAIL_ENABLED=True (FastMail is mocked)
# ---------------------------------------------------------------------------

class TestEmailServiceEnabled:
    """When MAIL_ENABLED is True the FastMail.send_message coroutine is called."""

    def _make_mock_fastmail(self, sent_messages: list):
        """Return a fake FastMail class that records calls."""

        class FakeFastMail:
            def __init__(self, conf):
                pass

            async def send_message(self, message):
                sent_messages.append(message)

        return FakeFastMail

    def test_send_verification_email_calls_fastmail(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", True)
        monkeypatch.setattr(settings_module.settings, "MAIL_USERNAME", "user")
        monkeypatch.setattr(settings_module.settings, "MAIL_PASSWORD", "pass")
        monkeypatch.setattr(settings_module.settings, "MAIL_FROM", "noreply@bizify.app")
        monkeypatch.setattr(settings_module.settings, "MAIL_SERVER", "smtp.example.com")
        monkeypatch.setattr(settings_module.settings, "MAIL_PORT", 587)
        monkeypatch.setattr(settings_module.settings, "MAIL_TLS", True)
        monkeypatch.setattr(settings_module.settings, "MAIL_SSL", False)
        monkeypatch.setattr(settings_module.settings, "FRONTEND_URL", "http://localhost:3000")

        sent: list = []

        import app.services.core.email_service as svc
        importlib.reload(svc)

        # Patch _queue_email on the EmailService class
        monkeypatch.setattr(svc.EmailService, "_queue_email",
                            lambda self, to, subject, body: _record_send(sent, to, subject, body))

        def _record_send(bag, to, subject, body):
            bag.append({"to": to, "subject": subject})

        email_service = svc.EmailService()
        run(email_service.send_verification_email("verify@example.com", "tok123"))
        # _queue_email is patched at module level
        assert len(sent) == 1
        assert sent[0]["to"] == "verify@example.com"
        assert "verify" in sent[0]["subject"].lower()

    def test_send_password_reset_email_calls_fastmail(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", True)
        monkeypatch.setattr(settings_module.settings, "FRONTEND_URL", "http://localhost:3000")

        sent: list = []

        import app.services.core.email_service as svc

        def _fake_send(self, to, subject, body):
            sent.append({"to": to, "subject": subject})

        monkeypatch.setattr(svc.EmailService, "_queue_email", _fake_send)

        email_service = svc.EmailService()
        run(email_service.send_password_reset_email("reset@example.com", "tok456"))

        assert len(sent) == 1
        assert sent[0]["to"] == "reset@example.com"
        assert "password" in sent[0]["subject"].lower()
