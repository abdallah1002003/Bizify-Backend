from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.ideation.idea import IdeaVersion
from app.models.business.business import BusinessRoadmap
from app.services.users import user_service
from app.services.ideation import idea_core as idea_service
from app.services.business import business_core as business_service
from app.services.business import business_roadmap
from app.services.billing import billing_service
from app.schemas.users.user import UserCreate
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate
from app.schemas.business.business import BusinessCreate
from app.models.enums import IdeaStatus, RoadmapStageStatus, UserRole, BusinessStage, StageType

def test_elite_idea_lifecycle(db: Session):
    """
    Verifies Phase 11 & 12 Idea logic:
    - Automatic snapshotting on creation and update.
    - RBAC enforcement via check_idea_access.
    """
    # 1. Create User
    user = user_service.create_user(db, UserCreate(
        name="Elite User",
        email=f"elite_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    # 2. Create Idea (triggers initial version)
    idea = idea_service.create_idea(db, IdeaCreate(
        owner_id=user.id,
        title="Evolutionary Idea",
        description="Initial logic",
        status=IdeaStatus.DRAFT,
        ai_score=0.5
    ))
    
    # Verify Versioning
    versions = db.query(IdeaVersion).filter(IdeaVersion.idea_id == idea.id).all()
    assert len(versions) == 1
    assert versions[0].snapshot_json["title"] == "Evolutionary Idea"
    
    # 3. Update Idea (triggers NEW version)
    idea_service.update_idea(db, idea, IdeaUpdate(
        title="Super Evolutionary Idea",
        owner_id=user.id 
    ))
    
    versions = db.query(IdeaVersion).filter(IdeaVersion.idea_id == idea.id).order_by(IdeaVersion.created_at.asc()).all()
    assert len(versions) == 2
    assert versions[1].snapshot_json["title"] == "Super Evolutionary Idea"
    
    # 4. RBAC Check
    another_user = user_service.create_user(db, UserCreate(
        name="Hacker User",
        email=f"hacker_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    assert idea_service.check_idea_access(db, idea.id, user.id) is True
    assert idea_service.check_idea_access(db, idea.id, another_user.id) is False

def test_elite_business_roadmap(db: Session):
    """
    Verifies Business Roadmap logic:
    - Automatic roadmap initialization on business creation.
    - Stage status transitions.
    """
    # 1. Create Business (triggers roadmap initialization)
    user = user_service.create_user(db, UserCreate(
        name="Biz Owner",
        email=f"biz_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    biz = business_service.create_business(db, BusinessCreate(
        owner_id=user.id,
        stage=BusinessStage.EARLY
    ))
    
    # Verify Roadmap
    roadmap = db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == biz.id).first()
    assert roadmap is not None
    
    # 2. Add Stages
    stage = business_roadmap.add_roadmap_stage(db, roadmap.id, StageType.RESEARCH, 0)
    assert stage.status == RoadmapStageStatus.PLANNED
    
    # 3. Transition Stage
    updated_stage = business_roadmap.update_stage_status(db, stage.id, RoadmapStageStatus.ACTIVE)
    assert updated_stage.status == RoadmapStageStatus.ACTIVE

def test_elite_billing_usage(db: Session):
    """
    Verifies Billing Usage logic:
    - Accurate usage recording.
    - Limit enforcement.
    """
    user = user_service.create_user(db, UserCreate(
        name="Billing User",
        email=f"billing_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    # 1. Record Usage
    usage = billing_service.record_usage(db, user.id, "AI_REQUEST", 5)
    assert usage.used == 5
    
    # 2. Check Limit (default True as no limit set)
    assert billing_service.check_usage_limit(db, user.id, "AI_REQUEST") is True
    
    # 3. Set Limit and Fail
    usage.limit_value = 10
    db.commit()
    
    billing_service.record_usage(db, user.id, "AI_REQUEST", 5)
    assert billing_service.check_usage_limit(db, user.id, "AI_REQUEST") is False
