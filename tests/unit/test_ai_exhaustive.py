"""Tests covering AI Services missing branches."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.services.ai.ai_service import AIService
from app.services.ai.embedding_service import EmbeddingService, get_embedding_service
from app.services.ai.provider_runtime import AIProviderService, get_ai_provider_service


# ── AIService ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_service_exhaustive():
    db = AsyncMock()
    svc = AIService(db)
    svc.validation_repo = AsyncMock()
    svc.embedding_repo = AsyncMock()
    svc.run_repo = AsyncMock()
    uid = uuid.uuid4()

    # line 103 execute_agent_run_async
    with patch("app.services.ai.ai_service.AgentRunService.execute_agent_run_async", new_callable=AsyncMock) as m_exec:
        await svc.execute_agent_run_async(uid)
        m_exec.assert_called_with(uid)

    # 125 delete_validation_log
    with patch.object(svc, "get_validation_log", new_callable=AsyncMock, return_value=None):
        assert await svc.delete_validation_log(uid) is None

    # 141 update_embedding
    await svc.update_embedding(MagicMock(), {"content": "ok"})
    svc.embedding_repo.update.assert_called()

    # 164-170 run_agent_in_background
    db_factory = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    db_factory.return_value = mock_ctx

    with patch("app.services.ai.ai_service.AgentRunService.execute_agent_run_async", new_callable=AsyncMock) as m_exec_bg:
        await AIService.run_agent_in_background(db_factory, uid)
        m_exec_bg.assert_called_with(uid)

    # run_agent_in_background Exception
    with patch("app.services.ai.ai_service.AgentRunService.execute_agent_run_async", new_callable=AsyncMock, side_effect=Exception("bg error")):
        await AIService.run_agent_in_background(db_factory, uid) # Should catch exception


# ── EmbeddingService ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_embedding_service_exhaustive():
    db = AsyncMock()
    svc = EmbeddingService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()

    # 22 get_embedding
    await svc.get_embedding(uid)
    # 26 get_embeddings
    await svc.get_embeddings()
    # 30 create_embedding
    await svc.create_embedding({"content": "a"})

    # 34-37 delete_embedding
    with patch.object(svc, "get_embedding", new_callable=AsyncMock, return_value=None):
        assert await svc.delete_embedding(uid) is None
        
    db_obj = MagicMock()
    with patch.object(svc, "get_embedding", new_callable=AsyncMock, return_value=db_obj):
        await svc.delete_embedding(uid)
        svc.repo.delete.assert_called_with(db_obj)

    # 47-53 trigger_vectorization
    assert await svc.trigger_vectorization(uid, "TARGET", "short") is None

    with patch("app.services.ai.provider_runtime.AIProviderService.generate_embedding_vector", new_callable=AsyncMock, return_value=[0.1, 0.2]):
        with patch.object(svc, "create_embedding", new_callable=AsyncMock, return_value=MagicMock(id=uid)) as m_create:
            res = await svc.trigger_vectorization(uid, "BUSINESS", "long text string long enough")
            assert res.id == uid
            m_create.assert_called()

    await get_embedding_service(db)


# ── AIProviderService ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_runtime_exhaustive():
    db = AsyncMock()
    svc = AIProviderService(db)

    from app.services.ai import provider_runtime
    
    # 42 _is_openai_enabled true
    with patch("app.services.ai.provider_runtime.settings") as mock_settings:
        mock_settings.AI_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "key"
        mock_settings.OPENAI_EMBEDDING_MODEL = "model"
        mock_settings.OPENAI_BASE_URL = "http://localhost/"
        mock_settings.AI_REQUEST_TIMEOUT_SECONDS = 10
        mock_settings.OPENAI_CHAT_MODEL = "gpt"
        
        assert provider_runtime._is_openai_enabled() is True

        # 99-123 _do_request embeddings
        # We need to simulate the circuit breaker calling _do_request
        # We can directly patch httpx.AsyncClient.post to return a mock response
        
        class MockResponse:
            def __init__(self, json_data):
                self._json_data = json_data
            def json(self):
                return self._json_data
            def raise_for_status(self):
                pass
                
        mock_resp = MockResponse({
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        })
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            vec = await svc._call_openai_embeddings("long text content")
            # 137 generate_embedding_vector
            res = await svc.generate_embedding_vector("long text content", dimensions=3)
            assert isinstance(res, list)

        # 150-200 _call_openai_agent_response
        # valid json
        mock_agent_resp = MockResponse({
            "choices": [{"message": {"content": '{"summary": "great", "score": 0.8}'}}]
        })
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_agent_resp):
            # 224 run_agent_execution returning output directly
            out = await svc.run_agent_execution({"input": 1}, agent_name="a", stage_type="s")
            assert out["mode"] == "openai"
            assert out["score"] == 0.8
            assert out["summary"] == "great"

        # invalid json fallback string
        mock_agent_resp_invalid = MockResponse({
            "choices": [{"message": {"content": "plain text response"}}]
        })
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_agent_resp_invalid):
            out2 = await svc._call_openai_agent_response({"input": 1}, agent_name="a", stage_type="s")
            assert out2["summary"] == "plain text response"
            
        # empty response
        mock_agent_resp_empty = MockResponse({
            "choices": [{"message": {"content": "   "}}]
        })
        # Circuit Breaker catches inner ValueError and raises Exception so _call returns None
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_agent_resp_empty):
            out3 = await svc._call_openai_agent_response({"input": 1}, agent_name="a", stage_type="s")
            assert out3 is None

    await get_ai_provider_service(db)
