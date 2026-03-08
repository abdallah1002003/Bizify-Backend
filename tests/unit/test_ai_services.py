# ruff: noqa
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch
import pytest_asyncio

from app.models.ai.agent import Agent
from app.models.business.business import BusinessRoadmap, RoadmapStage
from app.models.enums import AgentRunStatus
from app.schemas.ai.agent_run import AgentRunCreate
from app.services.ai.ai_service import initiate_agent_run, execute_agent_run_async, trigger_vectorization, record_validation_log

@pytest_asyncio.fixture
async def async_test_agent(async_db: AsyncSession):
    agent = Agent(name="Researcher Alpha", phase="research")
    async_db.add(agent)
    await async_db.commit()
    await async_db.refresh(agent)
    return agent

@pytest_asyncio.fixture
async def async_test_roadmap_stage(async_db: AsyncSession):
    # Create an independent user to avoid sync fixture conflicts
    from app.models.users.user import User
    from app.models.enums import UserRole
    from app.core.security import get_password_hash
    import uuid

    user = User(
        email=f"ai_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass"),
        name="Test User",
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)

    from app.models.business.business import Business
    from app.models.enums import BusinessStage
    biz = Business(owner_id=user.id, stage=BusinessStage.EARLY)
    async_db.add(biz)
    await async_db.commit()
    await async_db.refresh(biz)
    
    roadmap = BusinessRoadmap(business_id=biz.id)
    async_db.add(roadmap)
    await async_db.commit()
    await async_db.refresh(roadmap)
    
    from app.models.enums import StageType
    stage = RoadmapStage(roadmap_id=roadmap.id, order_index=1, stage_type=StageType.RESEARCH)
    async_db.add(stage)
    await async_db.commit()
    await async_db.refresh(stage)
    return stage

@pytest.mark.asyncio
@patch("app.services.ai.agent_run_service.provider_runtime.run_agent_execution")
@patch("app.services.billing.usage_service.UsageService.check_usage_limit", return_value=True)
@patch("app.services.billing.usage_service.UsageService.record_usage")
async def test_agent_run_lifecycle(mock_record_usage, mock_check_usage, mock_run_execution, async_db: AsyncSession, async_test_agent, async_test_roadmap_stage):
    # Mock the execution to return a specific result
    mock_run_execution.return_value = {
        "output": {"result": "mocked output"},
        "confidence_score": 0.92
    }

    # 1. Start run (PENDING)
    obj_in = AgentRunCreate(
        stage_id=async_test_roadmap_stage.id,
        agent_id=async_test_agent.id,
        input_data={"market": "tech"}
    )
    run = await initiate_agent_run(async_db, agent_id=async_test_agent.id, user_id=None, target_id=async_test_roadmap_stage.id, target_type="ROADMAP_STAGE", stage_id=async_test_roadmap_stage.id)
    assert run.status == AgentRunStatus.PENDING
    
    # 2. Execute run (Transition SUCCESS)
    updated_run = await execute_agent_run_async(async_db, run.id)
    assert updated_run.status == AgentRunStatus.SUCCESS
    assert updated_run.confidence_score == 0.92
    
    # 3. Record validation log
    log = await record_validation_log(async_db, updated_run.id, result="SUCCESS", details="Passed validation logic")
    assert log.threshold_passed is True
    assert log.agent_run_id == updated_run.id

@pytest.mark.asyncio
@patch("app.services.ai.embedding_service.provider_runtime.generate_embedding_vector")
async def test_embedding_generation_flow(mock_vector, async_db: AsyncSession, async_test_roadmap_stage):
    # Mock the embedding vector generation
    mock_vector.return_value = [0.1] * 1536

    content = "This is a roadmap for a new AI startup."
    embedding = await trigger_vectorization(async_db, target_id=async_test_roadmap_stage.id, target_type="ROADMAP_STAGE", content=content)
    assert len(embedding.vector) == 1536
    assert -1.0 <= float(embedding.vector[0]) <= 1.0
