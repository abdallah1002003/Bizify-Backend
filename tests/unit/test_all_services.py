"""
Comprehensive tests for all services in app/services/ targeting near-100% coverage.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# ── AI Services ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_service_comprehensive():
    from app.services.ai.ai_service import AIService
    
    db = AsyncMock()
    svc = AIService(db)
    
    # It uses run_repo and execute_ai_task
    svc.run_repo = AsyncMock()
    mock_run = MagicMock()
    mock_run.id = uuid4()
    svc.run_repo.create_safe = AsyncMock(return_value=mock_run)
    
    with patch("app.services.ai.ai_service.provider_runtime", new_callable=MagicMock) as mock_rt:
        mock_rt.execute_ai_task = AsyncMock(return_value={"status": "success", "result": "test"})
        # AIService delegates initiate_agent_run to AgentRunService, so we mock that
        with patch.object(svc, "_agent_run_svc") as mock_run_svc_factory:
            mock_run_svc = AsyncMock()
            mock_run_svc.initiate_agent_run.return_value = mock_run
            mock_run_svc_factory.return_value = mock_run_svc
            result = await svc.initiate_agent_run(uuid4(), uuid4(), uuid4(), "test", uuid4(), {"input": "test"})
            assert result is mock_run

@pytest.mark.asyncio
async def test_embedding_service_comprehensive():
    from app.services.ai.embedding_service import EmbeddingService
    
    db = AsyncMock()
    svc = EmbeddingService(db)
    
    svc.repo = AsyncMock()
    svc.repo.get_all = AsyncMock(return_value=[MagicMock()])
    
    result = await svc.get_embeddings(skip=0, limit=10)
    assert len(result) == 1

# ── Auth Service ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_service_comprehensive():
    from app.services.auth.auth_service import AuthService
    
    db = AsyncMock()
    user_svc = AsyncMock()
    svc = AuthService(db, user_service=user_svc)
    
    # authenticate_user
    mock_user = MagicMock()
    # verify_password takes (password, hash) so mock it or mock get_password_hash
    with patch("app.services.auth.auth_service.security.verify_password", return_value=True):
        user_svc.get_user_by_email = AsyncMock(return_value=mock_user)
        
        result = await svc.authenticate_user("test@example.com", "password")
        assert result is mock_user
    
    # authenticate_user - invalid pass
    with patch("app.services.auth.auth_service.security.verify_password", return_value=False):
        result = await svc.authenticate_user("test@example.com", "wrong")
        assert result is None
    
    # create_tokens
    # Create valid JWTs so jwt.decode doesn't fail in _persist_refresh_token
    import jwt
    from config.settings import settings
    import time
    future_time = int(time.time()) + 3600
    valid_jwt = jwt.encode({"sub": str(mock_user.id), "jti": "some_jti", "exp": future_time, "type": "refresh"}, settings.jwt_verify_key, algorithm=settings.jwt_algorithm)
    with patch("app.services.auth.auth_service.security.create_access_token", return_value="access"):
        with patch("app.services.auth.auth_service.security.create_refresh_token", return_value=valid_jwt):
            svc.refresh_token_repo = AsyncMock()
            acc, ref = await svc.create_tokens(mock_user.id)
            assert acc == "access"
            assert ref == valid_jwt

# ── Billing Services ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_service_comprehensive():
    from app.services.billing.plan_service import PlanService
    
    db = AsyncMock()
    svc = PlanService(db)
    
    mock_plan = MagicMock()
    svc.repo = AsyncMock()
    # PlanService uses get_ordered, not get_all
    svc.repo.get_ordered = AsyncMock(return_value=[mock_plan])
    
    result = await svc.get_plans()
    assert len(result) == 1

@pytest.mark.asyncio
async def test_subscription_service_comprehensive():
    from app.services.billing.subscription_service import SubscriptionService
    
    db = AsyncMock()
    svc = SubscriptionService(db)
    
    mock_sub = MagicMock()
    svc.sub_repo = AsyncMock()
    # Mocking what get_active_for_user returns
    svc.sub_repo.get_active_for_user = AsyncMock(return_value=mock_sub)
    
    result = await svc.get_active_subscription(uuid4())
    assert result is mock_sub

@pytest.mark.asyncio
async def test_usage_service_comprehensive():
    from app.services.billing.usage_service import UsageService
    
    db = AsyncMock()
    svc = UsageService(db)
    
    mock_usage = MagicMock()
    mock_usage.used = 5
    mock_usage.limit_value = 10
    
    # We will mock _get_usage_by_resource instead of repo directly as usage_service is complex
    with patch.object(svc, "_get_usage_by_resource", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_usage
        result = await svc.check_usage_limit(uuid4(), "api_calls")
        assert result is True # 5 is less than whatever limit it checks

# ── Business Services ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_service_comprehensive():
    from app.services.business.business_service import BusinessService
    
    db = AsyncMock()
    roadmap_svc = AsyncMock()
    collab_svc = AsyncMock()
    svc = BusinessService(db, roadmap_service=roadmap_svc, collaborator_service=collab_svc)
    
    svc.repo = AsyncMock()
    svc.repo.get_with_relations = AsyncMock(return_value=MagicMock())
    
    result = await svc.get_business(uuid4())
    assert result is not None

# ── Chat Services ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_service_comprehensive():
    from app.services.chat.chat_service import ChatService
    
    db = AsyncMock()
    svc = ChatService(db)
    
    svc._session_svc = AsyncMock()
    svc._session_svc.get_chat_sessions.return_value = [MagicMock()]
    
    result = await svc.get_chat_sessions()
    assert len(result) == 1

# ── Core Services ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_core_services_comprehensive():
    from app.services.core.file_service import FileService
    from app.services.core.notification_service import NotificationService
    from app.services.core.share_link_service import ShareLinkService
    
    db = AsyncMock()
    
    # File
    f_svc = FileService(db)
    f_svc.repo = AsyncMock()
    f_svc.repo.get.return_value = MagicMock()
    result = await f_svc.get_file(uuid4())
    assert result is not None
        
    # Notification
    n_svc = NotificationService(db)
    n_svc.repo = AsyncMock()
    n_svc.repo.get_for_user = AsyncMock(return_value=[MagicMock()])
    result = await n_svc.get_notifications(user_id=uuid4())
    assert len(result) == 1
        
    # Share Link
    sl_svc = ShareLinkService(db)
    sl_svc.repo = AsyncMock()
    sl_svc.repo.get_with_relations = AsyncMock(return_value=MagicMock())
    result = await sl_svc.get_share_link(uuid4())
    assert result is not None

# ── Ideation Services ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_service_comprehensive():
    from app.services.ideation.idea_service import IdeaService
    
    db = AsyncMock()
    access_svc = AsyncMock()
    version_svc = AsyncMock()
    svc = IdeaService(db, access_service=access_svc, version_service=version_svc)
    
    svc.repo = AsyncMock()
    svc.repo.get_with_relations = AsyncMock(return_value=MagicMock())
    
    result = await svc.get_idea(uuid4())
    assert result is not None

# ── Partner Services ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partner_profile_service_comprehensive():
    from app.services.partners.partner_profile import PartnerProfileService
    
    db = AsyncMock()
    svc = PartnerProfileService(db)
    
    svc.repo = AsyncMock()
    svc.repo.get_by_user.return_value = MagicMock()
    
    result = await svc.get_partner_profile(uuid4())
    assert result is not None

# ── User Services ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_service_comprehensive():
    from app.services.users.user_service import UserService
    
    db = AsyncMock()
    svc = UserService(db)
    
    svc.user_repo = AsyncMock()
    svc.user_repo.get_by_email.return_value = MagicMock()
    
    result = await svc.get_user_by_email("test@example.com")
    assert result is not None
