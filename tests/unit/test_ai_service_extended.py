# ruff: noqa
from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import AgentRunStatus, BusinessStage, StageType, UserRole
from app.schemas.business.business import BusinessCreate
from app.services.ai import ai_service
from app.services.business import business_service, business_roadmap
from sqlalchemy.ext.asyncio import AsyncSession


async def _create_user(async_db: AsyncSession, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix} User",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("securepassword123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


async def _create_business_stage(async_db: AsyncSession, owner_id):
    business = await business_service.create_business(
        async_db,
        BusinessCreate(owner_id=owner_id, stage=BusinessStage.EARLY),
    )
    roadmap = await business_roadmap.get_roadmap(async_db, business_id=business.id)
    stage = await business_roadmap.add_roadmap_stage(async_db, roadmap.id, StageType.RESEARCH, 1)
    return business, roadmap, stage


import pytest

@pytest.mark.asyncio
async def test_ai_service_success_paths_and_crud(async_db: AsyncSession, monkeypatch):
    test_user = await _create_user(async_db, "ai_primary")
    business, _, stage = await _create_business_stage(async_db, test_user.id)
    
    other_user = await _create_user(async_db, "ai_other")
    _, _, other_stage = await _create_business_stage(async_db, other_user.id)

    agent = await ai_service.create_agent(async_db, "Planner", "discovery", config={"x": 1})
    assert await ai_service.get_agent(async_db, agent.id) is not None
    agents_list = await ai_service.get_agents(async_db, skip=0, limit=10)
    assert len(agents_list) >= 1

    agent = await ai_service.update_agent(async_db, agent, {"name": "Planner v2"})
    assert agent.name == "Planner v2"

    run = await ai_service.initiate_agent_run(
        async_db,
        agent_id=agent.id,
        user_id=test_user.id,
        target_id=business.id,
        target_type="BUSINESS",
        stage_id=stage.id,
        input_data={"market": "ai"},
    )
    other_run = await ai_service.initiate_agent_run(
        async_db,
        agent_id=agent.id,
        user_id=other_user.id,
        target_id=business.id,
        target_type="BUSINESS",
        stage_id=other_stage.id,
        input_data={"market": "fintech"},
    )
    assert run.status == AgentRunStatus.PENDING
    assert other_run.status == AgentRunStatus.PENDING
    assert await ai_service.get_agent_run(async_db, run.id) is not None

    filtered_runs = await ai_service.get_agent_runs(async_db, user_id=test_user.id)
    assert len(filtered_runs) == 1
    assert filtered_runs[0].id == run.id

    async def mock_run_agent(*_args, **_kwargs): return {"summary": "done", "score": 0.88, "mode": "mock"}
    monkeypatch.setattr(
        ai_service.provider_runtime,
        "run_agent_execution",
        mock_run_agent,
    )
    executed = await ai_service.execute_agent_run_async(async_db, run.id)
    assert executed is not None
    assert executed.status == AgentRunStatus.SUCCESS
    assert executed.confidence_score == 0.88

    assert await ai_service.execute_agent_run_async(async_db, uuid4()) is None

    validation_logs = await ai_service.get_validation_logs(async_db, skip=0, limit=20)
    assert any(log.agent_run_id == run.id for log in validation_logs)

    extra_log = await ai_service.record_validation_log(async_db, run.id, result="FAILED", details="manual failure")
    assert extra_log.threshold_passed is False

    extra_log = await ai_service.update_validation_log(async_db, extra_log, {"threshold_passed": True})
    assert extra_log.threshold_passed is True
    assert await ai_service.get_validation_log(async_db, extra_log.id) is not None

    deleted_log = await ai_service.delete_validation_log(async_db, extra_log.id)
    assert deleted_log is not None
    assert await ai_service.delete_validation_log(async_db, extra_log.id) is None

    assert await ai_service.trigger_vectorization(
        async_db,
        target_id=business.id,
        target_type="BUSINESS",
        content="short",
        agent_id=agent.id,
    ) is None

    embedding = await ai_service.trigger_vectorization(
        async_db,
        target_id=business.id,
        target_type="BUSINESS",
        content="This is long enough to be vectorized by the service.",
        agent_id=agent.id,
    )
    assert embedding is not None
    assert embedding.business_id == business.id
    assert len(embedding.vector) == 1536

    extra_embedding = await ai_service.create_embedding(
        async_db,
        {
            "business_id": None,
            "agent_id": agent.id,
            "content": "additional embedding content",
            "vector": [0.1] * 1536,
        },
    )
    assert await ai_service.get_embedding(async_db, extra_embedding.id) is not None
    
    embed_list = await ai_service.get_embeddings(async_db, skip=0, limit=50)
    assert len(embed_list) >= 2

    extra_embedding = await ai_service.update_embedding(async_db, extra_embedding, {"content": "updated embedding"})
    assert extra_embedding.content == "updated embedding"

    run = await ai_service.update_agent_run(async_db, run, {"execution_time_ms": 42})
    assert run.execution_time_ms == 42

    deleted_embedding = await ai_service.delete_embedding(async_db, extra_embedding.id)
    assert deleted_embedding is not None
    assert await ai_service.delete_embedding(async_db, extra_embedding.id) is None

    deleted_run = await ai_service.delete_agent_run(async_db, other_run.id)
    assert deleted_run is not None
    assert await ai_service.delete_agent_run(async_db, other_run.id) is None

    throwaway_agent = await ai_service.create_agent(async_db, "Temp", "analysis")
    assert await ai_service.delete_agent(async_db, throwaway_agent.id) is not None
    assert await ai_service.delete_agent(async_db, throwaway_agent.id) is None

    status = await ai_service.get_detailed_status()
    assert status["module"] == "ai_service"
    assert status["status"] == "operational"
    await ai_service.reset_internal_state()


@pytest.mark.asyncio
async def test_ai_service_failure_path_marks_run_failed(async_db: AsyncSession, monkeypatch):
    test_user = await _create_user(async_db, "ai_fail")
    business, _, stage = await _create_business_stage(async_db, test_user.id)
    agent = await ai_service.create_agent(async_db, "Failure Agent", "validation")
    run = await ai_service.initiate_agent_run(
        async_db,
        agent_id=agent.id,
        user_id=None,
        target_id=business.id,
        target_type="BUSINESS",
        stage_id=stage.id,
        input_data={"mode": "fail"},
    )

    def _raise(*_args, **_kwargs):
        raise RuntimeError("provider failure")

    monkeypatch.setattr(ai_service.provider_runtime, "run_agent_execution", _raise)
    failed = await ai_service.execute_agent_run_async(async_db, run.id)
    assert failed is not None
    assert failed.status == AgentRunStatus.FAILED
    assert failed.confidence_score == 0.0
    assert failed.output_data["mode"] == "error"
    assert "provider failure" in failed.output_data["error"]

    from sqlalchemy import select
    stmt = select(models.ValidationLog).where(models.ValidationLog.agent_run_id == run.id)
    result = await async_db.execute(stmt)
    logs = result.scalars().all()
    assert logs
    assert any(log.threshold_passed is False for log in logs)
