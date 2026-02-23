import pytest
from app.services.ai import provider_runtime
from config.settings import settings


@pytest.mark.asyncio
async def test_generate_embedding_vector_is_stable_and_1536(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    vector_a = await provider_runtime.generate_embedding_vector("hello world")
    vector_b = await provider_runtime.generate_embedding_vector("hello world")

    assert len(vector_a) == 1536
    assert vector_a == vector_b


@pytest.mark.asyncio
async def test_run_agent_execution_uses_mock_without_openai_key(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    output = await provider_runtime.run_agent_execution(
        {"market": "ai"},
        agent_name="Planner",
        stage_type="research",
    )

    assert output["mode"] == "mock"
    assert output["score"] == 0.92
