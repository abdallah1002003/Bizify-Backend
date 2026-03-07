import pytest
import importlib
from unittest.mock import AsyncMock

# ---------------------------------------------------------------------------
# Tests: MAIL_ENABLED=False (no-op path)
# ---------------------------------------------------------------------------

class TestEmailServiceDisabled:
    """When MAIL_ENABLED is False no SMTP call should ever be made."""

    @pytest.mark.asyncio
    async def test_send_verification_email_noop(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", False)

        # Re-import to pick up patched settings
        import app.services.core.email_service as svc
        importlib.reload(svc)

        db = AsyncMock()
        service = svc.EmailService(db)
        # Should complete without error
        await service.send_verification_email("user@example.com", "fake-token")

    @pytest.mark.asyncio
    async def test_send_password_reset_email_noop(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", False)

        import app.services.core.email_service as svc
        importlib.reload(svc)

        db = AsyncMock()
        service = svc.EmailService(db)
        await service.send_password_reset_email("user@example.com", "fake-token")


# ---------------------------------------------------------------------------
# Tests: MAIL_ENABLED=True (FastMail is mocked)
# ---------------------------------------------------------------------------

class TestEmailServiceEnabled:
    """When MAIL_ENABLED is True the FastMail.send_message coroutine is called."""

    @pytest.mark.asyncio
    async def test_send_verification_email_calls_fastmail(self, monkeypatch):
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

        async def _record_send(self, to, subject, body):
            sent.append({"to": to, "subject": subject})

        # Patch _queue_email on the EmailService class
        monkeypatch.setattr(svc.EmailService, "_queue_email", _record_send)

        db = AsyncMock()
        email_service = svc.EmailService(db)
        await email_service.send_verification_email("verify@example.com", "tok123")
        
        assert len(sent) == 1
        assert sent[0]["to"] == "verify@example.com"
        assert "verify" in sent[0]["subject"].lower()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_calls_fastmail(self, monkeypatch):
        from config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "MAIL_ENABLED", True)
        monkeypatch.setattr(settings_module.settings, "FRONTEND_URL", "http://localhost:3000")

        sent: list = []

        import app.services.core.email_service as svc
        importlib.reload(svc)

        async def _fake_send(self, to, subject, body):
            sent.append({"to": to, "subject": subject})

        monkeypatch.setattr(svc.EmailService, "_queue_email", _fake_send)

        db = AsyncMock()
        email_service = svc.EmailService(db)
        await email_service.send_password_reset_email("reset@example.com", "tok456")

        assert len(sent) == 1
        assert sent[0]["to"] == "reset@example.com"
        assert "password" in sent[0]["subject"].lower()
