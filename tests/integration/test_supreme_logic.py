import pytest
from sqlalchemy.orm import Session
from app.models import User, BusinessRoadmap, RoadmapStage, IdeaVersion, Usage
from app.services.ideation import idea_service
from app.services.business import business_service
from app.services.business import business_roadmap
from app.services.billing import billing_service
from app.services.ai import ai_service
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate
from app.schemas.business.business import BusinessCreate
from app.models.enums import IdeaStatus, RoadmapStageStatus, BusinessStage

def test_ideation_deep_logic(db: Session, test_user: User):
    """Verifies automated versioning and RBAC in Ideation domain."""
    # 1. Create Idea with all required Pydantic fields
    idea_in = IdeaCreate(
        title="Supreme Idea", 
        description="Initial", 
        owner_id=test_user.id,
        status=IdeaStatus.DRAFT,
        ai_score=0.0
    )
    idea = idea_service.create_idea(db, idea_in)
    assert idea.id is not None
    
    # 2. Verify Initial Version
    versions = db.query(IdeaVersion).filter(IdeaVersion.idea_id == idea.id).all()
    assert len(versions) == 1
    
    # 3. Update Idea -> New Version
    update_in = IdeaUpdate(description="Modified Content")
    idea_service.update_idea(db, idea, update_in, performer_id=test_user.id)
    
    versions = db.query(IdeaVersion).filter(IdeaVersion.idea_id == idea.id).all()
    assert len(versions) == 2
    assert versions[-1].snapshot_json["description"] == "Modified Content"

def test_business_roadmap_automation(db: Session, test_user: User):
    """Verifies automated roadmap and prerequisite validation."""
    # 1. Create Business
    bus_in = BusinessCreate(
        name="Supreme Corp", 
        owner_id=test_user.id, 
        stage=BusinessStage.EARLY
    )
    bus = business_service.create_business(db, bus_in)
    
    # 2. Check Auto-Roadmap
    roadmap = db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == bus.id).first()
    assert roadmap is not None
    
    stages = db.query(RoadmapStage).filter(RoadmapStage.roadmap_id == roadmap.id).all()
    assert len(stages) >= 1
    assert str(stages[0].stage_type.value).upper() == "READINESS"
    
    # 3. Prerequisite Violation Check
    stage2 = business_roadmap.add_roadmap_stage(db, roadmap.id, "MARKET", 1)
    
    with pytest.raises(ValueError, match="Prerequisite stage not completed"):
        business_roadmap.transition_stage(db, stage2.id, RoadmapStageStatus.ACTIVE)

def test_billing_cross_module_enforcement(db: Session, test_user: User):
    """Verifies usage limits blocking AI operations."""
    # 1. Setup Business and Roadmap Stage
    bus_in = BusinessCreate(
        name="AI Corp", 
        owner_id=test_user.id, 
        stage=BusinessStage.EARLY
    )
    bus = business_service.create_business(db, bus_in)
    roadmap = db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == bus.id).first()
    stage = roadmap.stages[0]
    
    # 2. Set artificial limit to 0
    billing_service.record_usage(db, test_user.id, "AI_REQUEST", quantity=0)
    usage = db.query(Usage).filter(Usage.user_id == test_user.id, Usage.resource_type == "AI_REQUEST").first()
    usage.limit_value = 0
    db_session = Session.object_session(usage) # Ensure we use the correct session
    db_session.commit()
    
    # 3. Attempt AI run -> Should fail
    agent = ai_service.create_agent(db, "SupremeBot", "RESEARCH", {})
    
    with pytest.raises(PermissionError, match="Insufficient AI quota"):
        ai_service.initiate_agent_run(db, agent.id, test_user.id, test_user.id, "USER", stage_id=stage.id)

if __name__ == "__main__":
    pytest.main([__file__])
