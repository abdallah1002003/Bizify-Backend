"""Tests for remaining core services and tiny ideation gaps to push coverage higher."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.services.core.cleanup_service import CleanupService, get_cleanup_service
from app.services.core.core_service import CoreService, get_core_service
from app.services.core.email_service import (
    EmailService, register_email_handlers
)
from app.services.ideation.idea_comparison import (
    IdeaComparisonService, get_idea_comparison_service
)


# ── CleanupService ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cleanup_service_exhaustive():
    db = AsyncMock()
    svc = CleanupService(db=db)
    svc.refresh_token_repo = AsyncMock()
    svc.password_reset_token_repo = AsyncMock()
    svc.email_verify_token_repo = AsyncMock()

    # Success paths: returns deleted count
    svc.refresh_token_repo.delete_expired.return_value = 3
    svc.password_reset_token_repo.delete_expired_or_used.return_value = 2
    svc.email_verify_token_repo.delete_expired_or_used.return_value = 1

    result = await svc.cleanup_expired_refresh_tokens()
    assert result == 3

    result = await svc.cleanup_expired_password_reset_tokens()
    assert result == 2

    result = await svc.cleanup_expired_verification_tokens()
    assert result == 1

    # Success paths: returns 0 (no log line for zero deletions)
    svc.refresh_token_repo.delete_expired.return_value = 0
    result = await svc.cleanup_expired_refresh_tokens()
    assert result == 0

    # Error paths: exceptions trigger rollback and return 0
    svc.refresh_token_repo.delete_expired.side_effect = Exception("db fail")
    result = await svc.cleanup_expired_refresh_tokens()
    assert result == 0
    svc.refresh_token_repo.delete_expired.side_effect = None

    svc.password_reset_token_repo.delete_expired_or_used.side_effect = Exception("db fail")
    result = await svc.cleanup_expired_password_reset_tokens()
    assert result == 0
    svc.password_reset_token_repo.delete_expired_or_used.side_effect = None

    svc.email_verify_token_repo.delete_expired_or_used.side_effect = Exception("db fail")
    result = await svc.cleanup_expired_verification_tokens()
    assert result == 0
    svc.email_verify_token_repo.delete_expired_or_used.side_effect = None

    # cleanup_all
    svc.refresh_token_repo.delete_expired.return_value = 5
    svc.password_reset_token_repo.delete_expired_or_used.return_value = 3
    svc.email_verify_token_repo.delete_expired_or_used.return_value = 2
    result = await svc.cleanup_all()
    assert result["refresh_tokens"] == 5
    assert result["password_reset_tokens"] == 3
    assert result["verification_tokens"] == 2

    # Dependency provider
    await get_cleanup_service(db)


# ── CoreService ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_core_service_exhaustive():
    db = AsyncMock()
    svc = CoreService(db=db)
    uid = uuid.uuid4()
    user_id = uuid.uuid4()

    # All delegated methods — patch underlying services to avoid DB calls
    with patch("app.services.core.core_service.FileService") as MockFile, \
         patch("app.services.core.core_service.NotificationService") as MockNotif:
        # Setup file mock
        file_inst = AsyncMock()
        MockFile.return_value = file_inst

        # Setup notif mock
        notif_inst = AsyncMock()
        MockNotif.return_value = notif_inst

        await svc.get_file(uid)
        await svc.get_files()
        await svc.get_files(owner_id=user_id)
        await svc.create_file({"filename": "f.pdf"})
        await svc.update_file(MagicMock(), {"filename": "g.pdf"})
        await svc.delete_file(uid)

        await svc.get_notification(uid)
        await svc.get_notifications()
        await svc.get_notifications(user_id=user_id)
        await svc.create_notification({"message": "hi"})
        await svc.update_notification(MagicMock(), {"message": "bye"})
        await svc.delete_notification(uid)

    # Status helpers
    result = svc.get_detailed_status()
    assert result["module"] == "core_service"
    svc.reset_internal_state()

    # Dependency provider
    await get_core_service(db)


# ── EmailService ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_email_service_exhaustive():
    db = AsyncMock()
    svc = EmailService(db=db)

    # register_email_handlers (just subscribes, no assertion needed)
    register_email_handlers()

    # render_template: success with existing template renders something
    with patch("app.services.core.email_service.jinja_env") as mock_env:
        mock_tmpl = MagicMock()
        mock_tmpl.render.return_value = "<html>ok</html>"
        mock_env.get_template.return_value = mock_tmpl
        result = svc.render_template("base.html", heading="Hello")
        assert "<html>" in result

    # render_template: template error → fallback html
    with patch("app.services.core.email_service.jinja_env") as mock_env:
        mock_env.get_template.side_effect = Exception("missing template")
        result = svc.render_template("missing.html", content_html="<p>fallback</p>")
        assert "<html>" in result

    # _queue_email: success
    with patch("app.repositories.core_repository.EmailMessageRepository") as MockRepo:
        repo_inst = AsyncMock()
        MockRepo.return_value = repo_inst
        await svc._queue_email("test@test.com", "Subject", "<html>body</html>")

    # _queue_email: repo.create raises exception → rollback
    with patch("app.repositories.core_repository.EmailMessageRepository") as MockRepo:
        repo_inst = AsyncMock()
        repo_inst.create.side_effect = Exception("db fail")
        MockRepo.return_value = repo_inst
        await svc._queue_email("fail@test.com", "Subj", "<html/>")
        repo_inst.rollback.assert_called_once()

    # send_verification_email
    with patch.object(svc, "_queue_email", new_callable=AsyncMock) as m_queue, \
         patch.object(svc, "render_template", return_value="<html/>") as _m_tmpl:
        await svc.send_verification_email("u@t.com", "tok123")
        m_queue.assert_called_once()

    # send_password_reset_email
    with patch.object(svc, "_queue_email", new_callable=AsyncMock) as m_queue2, \
         patch.object(svc, "render_template", return_value="<html/>"):
        await svc.send_password_reset_email("u@t.com", "rtok")
        m_queue2.assert_called_once()

    # handle_auth_event: missing email → early return
    await EmailService.handle_auth_event("auth.user_registered", {"token": "t"})

    # handle_auth_event: missing token → early return
    await EmailService.handle_auth_event("auth.user_registered", {"email": "e@t.com"})

    # handle_auth_event: user_registered
    with patch("app.db.database.AsyncSessionLocal") as MockSession:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        MockSession.return_value = mock_ctx

        with patch.object(EmailService, "send_verification_email", new_callable=AsyncMock):
            await EmailService.handle_auth_event(
                "auth.user_registered", {"email": "u@t.com", "token": "tok"}
            )

    # handle_auth_event: password_reset_requested
    with patch("app.db.database.AsyncSessionLocal") as MockSession2:
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx2.__aexit__ = AsyncMock(return_value=False)
        MockSession2.return_value = mock_ctx2

        with patch.object(EmailService, "send_password_reset_email", new_callable=AsyncMock):
            await EmailService.handle_auth_event(
                "auth.password_reset_requested", {"email": "u@t.com", "token": "rtok"}
            )

    # handle_auth_event: unknown event type (no branch hit)
    with patch("app.db.database.AsyncSessionLocal") as MockSession3:
        mock_ctx3 = AsyncMock()
        mock_ctx3.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx3.__aexit__ = AsyncMock(return_value=False)
        MockSession3.return_value = mock_ctx3

        await EmailService.handle_auth_event(
            "auth.unknown_event", {"email": "u@t.com", "token": "tok"}
        )


# ── IdeaComparisonService (1-line gap: create_comparison) ─────────────────────

@pytest.mark.asyncio
async def test_idea_comparison_service_create_comparison():
    db = AsyncMock()
    svc = IdeaComparisonService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    user_id = uuid.uuid4()

    # CRUD coverage
    await svc.get_idea_comparison(uid)
    await svc.get_idea_comparisons()
    await svc.create_idea_comparison({"name": "test", "user_id": user_id})
    await svc.update_idea_comparison(MagicMock(), {"name": "new"})
    await svc.delete_idea_comparison(uid)

    # The 1 uncovered line: create_comparison helper (line 47)
    await svc.create_comparison("My Comparison", user_id)
    svc.repo.create.assert_called()

    # Dependency provider
    await get_idea_comparison_service(db)
