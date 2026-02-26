import pytest
from unittest.mock import patch
from app.services.ai.provider_runtime import (
    _normalize_score,
    _normalize_vector,
    _deterministic_vector,
    _mock_agent_response,
    generate_embedding_vector,
    run_agent_execution
)

def test_normalize_score():
    assert _normalize_score(0.5) == 0.5
    assert _normalize_score(1.5) == 1.0
    assert _normalize_score(-0.5) == 0.0
    assert _normalize_score("0.7") == 0.7
    assert _normalize_score("invalid", default=0.5) == 0.5

def test_normalize_vector():
    v = [1.0, 2.0]
    assert _normalize_vector(v, 2) == v
    assert _normalize_vector(v, 3) == [1.0, 2.0, 0.0]
    assert _normalize_vector(v, 1) == [1.0]

def test_deterministic_vector():
    v1 = _deterministic_vector("test", 1536)
    v2 = _deterministic_vector("test", 1536)
    v3 = _deterministic_vector("other", 1536)
    assert v1 == v2
    assert v1 != v3
    assert len(v1) == 1536

def test_mock_agent_response():
    resp = _mock_agent_response({"key": "val"}, agent_name="test_agent", stage_type="ideation")
    assert resp["mode"] == "mock"
    assert "test_agent" in resp["summary"]
    assert "ideation" in resp["summary"]
    assert "context_keys=key" in resp["highlights"][0]

@pytest.mark.asyncio
async def test_generate_embedding_vector_fallback():
    # Force OpenAI disabled
    with patch("app.services.ai.provider_runtime._is_openai_enabled", return_value=False):
        v = await generate_embedding_vector("hello", dimensions=10)
        assert len(v) == 10
        # Should be deterministic
        v2 = await generate_embedding_vector("hello", dimensions=10)
        assert v == v2

@pytest.mark.asyncio
async def test_run_agent_execution_mock_fallback():
    # Force OpenAI disabled
    with patch("app.services.ai.provider_runtime._is_openai_enabled", return_value=False):
        resp = await run_agent_execution({"q": "test"}, agent_name="AgentA", stage_type="T")
        assert resp["mode"] == "mock"
        assert "AgentA" in resp["summary"]
