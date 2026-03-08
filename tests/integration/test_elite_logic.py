import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ideation.idea import IdeaVersion
from app.models.business.business import BusinessRoadmap
from app.services.users.user_service import UserService
from app.services.ideation.idea_service import IdeaService
from app.services.ideation.idea_version import IdeaVersionService
from app.services.ideation.idea_access import IdeaAccessService
from app.services.business.business_service import BusinessService
from app.services.business.business_roadmap import BusinessRoadmapService
from app.services.business.business_collaborator import BusinessCollaboratorService
from app.services.billing.usage_service import UsageService
from app.schemas.users.user import UserCreate
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate
from app.schemas.business.business import BusinessCreate
from app.models.enums import IdeaStatus, RoadmapStageStatus, UserRole, BusinessStage, StageType

@pytest.mark.asyncio
async def test_elite_idea_lifecycle(async_db: AsyncSession):
    """
    Verifies Phase 11 & 12 Idea logic:
    - Automatic snapshotting on creation and update.
    - RBAC enforcement via check_idea_access.
    """
    user_svc = UserService(async_db)
    access_svc = IdeaAccessService(async_db)
    idea_svc = IdeaService(async_db, access_svc, IdeaVersionService(async_db))
    
    # 1. Create User
    user = await user_svc.create_user(UserCreate(
        name="Elite User",
        email=f"elite_{uuid4().hex[:8]}@example.com",
        password="strong_password"
    ))
    
    # 2. Create Idea (triggers initial version)
    idea = await idea_svc.create_idea(IdeaCreate(
        owner_id=user.id,
        title="Evolutionary Idea",
        description="Initial logic",
        status=IdeaStatus.DRAFT,
        ai_score=0.5
    ))
    
    # Verify Versioning
    stmt = select(IdeaVersion).where(IdeaVersion.idea_id == idea.id)
    versions = (await async_db.execute(stmt)).scalars().all()
    assert len(versions) == 1
    assert versions[0].snapshot_json["title"] == "Evolutionary Idea"
    
    # 3. Update Idea (triggers NEW version)
    await idea_svc.update_idea(idea, IdeaUpdate(
        title="Super Evolutionary Idea",
        owner_id=user.id 
    ))
    
    stmt = select(IdeaVersion).where(IdeaVersion.idea_id == idea.id).order_by(IdeaVersion.created_at.asc())
    versions = (await async_db.execute(stmt)).scalars().all()
    assert len(versions) == 2
    assert versions[1].snapshot_json["title"] == "Super Evolutionary Idea"
    
    # 4. RBAC Check
    another_user = await user_svc.create_user(UserCreate(
        name="Hacker User",
        email=f"hacker_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    assert await access_svc.check_idea_access(idea.id, user.id) is True
    assert await access_svc.check_idea_access(idea.id, another_user.id) is False

@pytest.mark.asyncio
async def test_elite_business_roadmap(async_db: AsyncSession):
    """
    Verifies Business Roadmap logic:
    - Automatic roadmap initialization on business creation.
    - Stage status transitions.
    """
    user_svc = UserService(async_db)
    roadmap_svc = BusinessRoadmapService(async_db)
    collab_svc = BusinessCollaboratorService(async_db)
    biz_svc = BusinessService(async_db, roadmap_svc, collab_svc)
    
    # 1. Create Business (triggers roadmap initialization)
    user = await user_svc.create_user(UserCreate(
        name="Biz Owner",
        email=f"biz_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    biz = await biz_svc.create_business(BusinessCreate(
        owner_id=user.id,
        stage=BusinessStage.EARLY
    ))
    
    # Verify Roadmap
    stmt = select(BusinessRoadmap).where(BusinessRoadmap.business_id == biz.id)
    roadmap = (await async_db.execute(stmt)).scalars().first()
    assert roadmap is not None
    
    # 2. Add Stages
    stage = await roadmap_svc.add_roadmap_stage(roadmap.id, StageType.RESEARCH, 0)
    assert stage.status == RoadmapStageStatus.PLANNED
    
    # 3. Transition Stage
    updated_stage = await roadmap_svc.transition_stage(stage.id, RoadmapStageStatus.ACTIVE)
    assert updated_stage.status == RoadmapStageStatus.ACTIVE

@pytest.mark.asyncio
async def test_elite_billing_usage(async_db: AsyncSession):
    """
    Verifies Billing Usage logic:
    - Accurate usage recording.
    - Limit enforcement.
    """
    user_svc = UserService(async_db)
    usage_svc = UsageService(async_db)
    
    user = await user_svc.create_user(UserCreate(
        name="Billing User",
        email=f"billing_{uuid4().hex[:8]}@example.com",
        password="strong_password",
        role=UserRole.ENTREPRENEUR
    ))
    
    # 1. Record Usage
    usage = await usage_svc.record_usage(user.id, "AI_REQUEST", 5)
    assert usage.used == 5
    
    # 2. Check Limit (default True as no limit set)
    assert await usage_svc.check_usage_limit(user.id, "AI_REQUEST") is True
    
    # 3. Set Limit and Fail
    usage.limit_value = 10
    await async_db.commit()
    
    await usage_svc.record_usage(user.id, "AI_REQUEST", 5)
    assert await usage_svc.check_usage_limit(user.id, "AI_REQUEST") is False
