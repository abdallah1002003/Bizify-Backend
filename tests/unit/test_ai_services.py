import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.ai.agent import Agent
from app.models.business.business import BusinessRoadmap, RoadmapStage
from app.models.enums import AgentRunStatus
from app.schemas.ai.agent_run import AgentRunCreate
from app.services.ai.ai_service import initiate_agent_run, execute_agent_run_async, trigger_vectorization, record_validation_log

@pytest.fixture
def test_agent(db: Session):
    agent = Agent(name="Researcher Alpha", phase="research")
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@pytest.fixture
def test_roadmap_stage(db: Session, test_user):
    # Need a business first (simplified mock)
    from app.models.business.business import Business
    from app.models.enums import BusinessStage
    biz = Business(owner_id=test_user.id, stage=BusinessStage.EARLY)
    db.add(biz)
    db.commit()
    
    roadmap = BusinessRoadmap(business_id=biz.id)
    db.add(roadmap)
    db.commit()
    
    from app.models.enums import StageType
    stage = RoadmapStage(roadmap_id=roadmap.id, order_index=1, stage_type=StageType.RESEARCH)
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage

@pytest.mark.asyncio
@patch("app.services.ai.agent_run_service.provider_runtime.run_agent_execution")
@patch("app.services.billing.usage_service.UsageService.check_usage_limit", return_value=True)
@patch("app.services.billing.usage_service.UsageService.record_usage")
async def test_agent_run_lifecycle(mock_record_usage, mock_check_usage, mock_run_execution, db: Session, test_agent, test_roadmap_stage):
    # Mock the execution to return a specific result
    mock_run_execution.return_value = {
        "output": {"result": "mocked output"},
        "confidence_score": 0.92
    }

    # 1. Start run (PENDING)
    obj_in = AgentRunCreate(
        stage_id=test_roadmap_stage.id,
        agent_id=test_agent.id,
        input_data={"market": "tech"}
    )
    run = initiate_agent_run(db, agent_id=test_agent.id, user_id=None, target_id=test_roadmap_stage.id, target_type="ROADMAP_STAGE", stage_id=test_roadmap_stage.id)
    assert run.status == AgentRunStatus.PENDING
    
    # 2. Execute run (Transition SUCCESS)
    updated_run = await execute_agent_run_async(db, run.id)
    assert updated_run.status == AgentRunStatus.SUCCESS
    assert updated_run.confidence_score == 0.92
    
    # 3. Record validation log
    log = record_validation_log(db, updated_run.id, result="SUCCESS", details="Passed validation logic")
    assert log.threshold_passed is True
    assert log.agent_run_id == updated_run.id

@pytest.mark.asyncio
@patch("app.services.ai.embedding_service.provider_runtime.generate_embedding_vector")
async def test_embedding_generation_flow(mock_vector, db: Session, test_roadmap_stage):
    # Mock the embedding vector generation
    mock_vector.return_value = [0.1] * 1536

    content = "This is a roadmap for a new AI startup."
    embedding = await trigger_vectorization(db, target_id=test_roadmap_stage.id, target_type="ROADMAP_STAGE", content=content)
    assert len(embedding.vector) == 1536
    assert -1.0 <= float(embedding.vector[0]) <= 1.0
