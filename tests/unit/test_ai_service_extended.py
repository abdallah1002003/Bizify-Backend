from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import AgentRunStatus, BusinessStage, StageType, UserRole
from app.schemas.business.business import BusinessCreate
from app.services.ai import ai_service
from app.services.business import business_service, business_roadmap


def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix} User",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("securepassword123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_business_stage(db, owner_id):
    business = business_service.create_business(
        db,
        BusinessCreate(owner_id=owner_id, stage=BusinessStage.EARLY),
    )
    roadmap = business_roadmap.get_roadmap(db, business_id=business.id)
    stage = business_roadmap.add_roadmap_stage(db, roadmap.id, StageType.RESEARCH, 1)
    return business, roadmap, stage


import pytest

@pytest.mark.asyncio
async def test_ai_service_success_paths_and_crud(db, test_user, monkeypatch):
    business, _, stage = _create_business_stage(db, test_user.id)
    other_user = _create_user(db, "ai_other")
    _, _, other_stage = _create_business_stage(db, other_user.id)

    agent = ai_service.create_agent(db, "Planner", "discovery", config={"x": 1})
    assert ai_service.get_agent(db, agent.id) is not None
    assert len(ai_service.get_agents(db, skip=0, limit=10)) >= 1

    agent = ai_service.update_agent(db, agent, {"name": "Planner v2"})
    assert agent.name == "Planner v2"

    run = ai_service.initiate_agent_run(
        db,
        agent_id=agent.id,
        user_id=test_user.id,
        target_id=business.id,
        target_type="BUSINESS",
        stage_id=stage.id,
        input_data={"market": "ai"},
    )
    other_run = ai_service.initiate_agent_run(
        db,
        agent_id=agent.id,
        user_id=other_user.id,
        target_id=business.id,
        target_type="BUSINESS",
        stage_id=other_stage.id,
        input_data={"market": "fintech"},
    )
    assert run.status == AgentRunStatus.PENDING
    assert other_run.status == AgentRunStatus.PENDING
    assert ai_service.get_agent_run(db, run.id) is not None

    filtered_runs = ai_service.get_agent_runs(db, user_id=test_user.id)
    assert len(filtered_runs) == 1
    assert filtered_runs[0].id == run.id

    async def mock_run_agent(*_args, **_kwargs): return {"summary": "done", "score": 0.88, "mode": "mock"}
    monkeypatch.setattr(
        ai_service.provider_runtime,
        "run_agent_execution",
        mock_run_agent,
    )
    executed = await ai_service.execute_agent_run_async(db, run.id)
    assert executed is not None
    assert executed.status == AgentRunStatus.SUCCESS
    assert executed.confidence_score == 0.88

    assert await ai_service.execute_agent_run_async(db, uuid4()) is None

    validation_logs = ai_service.get_validation_logs(db, skip=0, limit=20)
    assert any(log.agent_run_id == run.id for log in validation_logs)

    extra_log = ai_service.record_validation_log(db, run.id, result="FAILED", details="manual failure")
    assert extra_log.threshold_passed is False

    extra_log = ai_service.update_validation_log(db, extra_log, {"threshold_passed": True})
    assert extra_log.threshold_passed is True
    assert ai_service.get_validation_log(db, extra_log.id) is not None

    deleted_log = ai_service.delete_validation_log(db, extra_log.id)
    assert deleted_log is not None
    assert ai_service.delete_validation_log(db, extra_log.id) is None

    assert await ai_service.trigger_vectorization(
        db,
        target_id=business.id,
        target_type="BUSINESS",
        content="short",
        agent_id=agent.id,
    ) is None

    embedding = await ai_service.trigger_vectorization(
        db,
        target_id=business.id,
        target_type="BUSINESS",
        content="This is long enough to be vectorized by the service.",
        agent_id=agent.id,
    )
    assert embedding is not None
    assert embedding.business_id == business.id
    assert len(embedding.vector) == 1536

    extra_embedding = ai_service.create_embedding(
        db,
        {
            "business_id": None,
            "agent_id": agent.id,
            "content": "additional embedding content",
            "vector": [0.1] * 1536,
        },
    )
    assert ai_service.get_embedding(db, extra_embedding.id) is not None
    assert len(ai_service.get_embeddings(db, skip=0, limit=50)) >= 2

    extra_embedding = ai_service.update_embedding(db, extra_embedding, {"content": "updated embedding"})
    assert extra_embedding.content == "updated embedding"

    run = ai_service.update_agent_run(db, run, {"execution_time_ms": 42})
    assert run.execution_time_ms == 42

    deleted_embedding = ai_service.delete_embedding(db, extra_embedding.id)
    assert deleted_embedding is not None
    assert ai_service.delete_embedding(db, extra_embedding.id) is None

    deleted_run = ai_service.delete_agent_run(db, other_run.id)
    assert deleted_run is not None
    assert ai_service.delete_agent_run(db, other_run.id) is None

    throwaway_agent = ai_service.create_agent(db, "Temp", "analysis")
    assert ai_service.delete_agent(db, throwaway_agent.id) is not None
    assert ai_service.delete_agent(db, throwaway_agent.id) is None

    status = ai_service.get_detailed_status()
    assert status["module"] == "ai_service"
    assert status["status"] == "operational"
    ai_service.reset_internal_state()


@pytest.mark.asyncio
async def test_ai_service_failure_path_marks_run_failed(db, test_user, monkeypatch):
    business, _, stage = _create_business_stage(db, test_user.id)
    agent = ai_service.create_agent(db, "Failure Agent", "validation")
    run = ai_service.initiate_agent_run(
        db,
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
    failed = await ai_service.execute_agent_run_async(db, run.id)
    assert failed is not None
    assert failed.status == AgentRunStatus.FAILED
    assert failed.confidence_score == 0.0
    assert failed.output_data["mode"] == "error"
    assert "provider failure" in failed.output_data["error"]

    logs = (
        db.query(models.ValidationLog)
        .filter(models.ValidationLog.agent_run_id == run.id)
        .all()
    )
    assert logs
    assert any(log.threshold_passed is False for log in logs)
