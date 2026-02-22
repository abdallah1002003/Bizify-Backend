import pytest
from sqlalchemy.orm import Session
from app.models.ai.agent import Agent
from app.models.business.business import BusinessRoadmap, RoadmapStage
from app.models.enums import AgentRunStatus
from app.schemas.ai.agent_run import AgentRunCreate
from app.services.ai.agent_run_service import create_agent_run, execute_agent_run
from app.services.ai.validation_log_service import record_critique
from app.services.ai.embedding_service import generate_embedding

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

def test_agent_run_lifecycle(db: Session, test_agent, test_roadmap_stage):
    # 1. Start run (PENDING)
    obj_in = AgentRunCreate(
        stage_id=test_roadmap_stage.id,
        agent_id=test_agent.id,
        input_data={"market": "tech"}
    )
    run = create_agent_run(db, obj_in)
    assert run.status == AgentRunStatus.PENDING
    
    # 2. Execute run (Transition SUCCESS)
    updated_run = execute_agent_run(db, run.id)
    assert updated_run.status == AgentRunStatus.SUCCESS
    assert updated_run.confidence_score == 0.92
    
    # 3. Record critique
    log = record_critique(db, updated_run.id, score=0.92, critique={"logic": "valid"})
    assert log.threshold_passed is True
    assert log.agent_run_id == updated_run.id

def test_embedding_generation(db: Session, test_agent):
    content = "This is a roadmap for a new AI startup."
    embedding = generate_embedding(db, content=content, agent_id=test_agent.id)
    assert embedding.content == content
    assert len(embedding.vector) == 1536
    assert -1.0 <= float(embedding.vector[0]) <= 1.0
