import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, BusinessRoadmap, RoadmapStage, IdeaVersion, Usage
from app.services.ideation.idea_service import IdeaService
from app.services.ideation.idea_version import IdeaVersionService
from app.services.ideation.idea_access import IdeaAccessService
from app.services.business.business_service import BusinessService
from app.services.business.business_roadmap import BusinessRoadmapService
from app.services.business.business_collaborator import BusinessCollaboratorService
from app.services.billing.usage_service import UsageService
from app.services.ai.ai_service import AIService
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate
from app.schemas.business.business import BusinessCreate
from app.models.enums import IdeaStatus, RoadmapStageStatus, BusinessStage

@pytest.mark.asyncio
async def test_ideation_deep_logic(async_db: AsyncSession, test_user: User):
    """Verifies automated versioning and RBAC in Ideation domain."""
    access_svc = IdeaAccessService(async_db)
    idea_svc = IdeaService(async_db, access_svc, IdeaVersionService(async_db))
    # 1. Create Idea with all required Pydantic fields
    idea_in = IdeaCreate(
        title="Supreme Idea", 
        description="Initial", 
        owner_id=test_user.id,
        status=IdeaStatus.DRAFT,
        ai_score=0.0
    )
    idea = await idea_svc.create_idea(idea_in)
    assert idea.id is not None
    
    # 2. Verify Initial Version
    stmt = select(IdeaVersion).where(IdeaVersion.idea_id == idea.id)
    versions = (await async_db.execute(stmt)).scalars().all()
    assert len(versions) == 1
    
    # 3. Update Idea -> New Version
    update_in = IdeaUpdate(description="Modified Content")
    await idea_svc.update_idea(idea, update_in, performer_id=test_user.id)
    
    stmt = select(IdeaVersion).where(IdeaVersion.idea_id == idea.id)
    versions = (await async_db.execute(stmt)).scalars().all()
    assert len(versions) == 2
    assert versions[-1].snapshot_json["description"] == "Modified Content"

@pytest.mark.asyncio
async def test_business_roadmap_automation(async_db: AsyncSession, test_user: User):
    """Verifies automated roadmap and prerequisite validation."""
    roadmap_svc = BusinessRoadmapService(async_db)
    collab_svc = BusinessCollaboratorService(async_db)
    biz_svc = BusinessService(async_db, roadmap_svc, collab_svc)
    
    # 1. Create Business
    bus_in = BusinessCreate(
        name="Supreme Corp", 
        owner_id=test_user.id, 
        stage=BusinessStage.EARLY
    )
    bus = await biz_svc.create_business(bus_in)
    
    # 2. Check Auto-Roadmap
    stmt = select(BusinessRoadmap).where(BusinessRoadmap.business_id == bus.id)
    roadmap = (await async_db.execute(stmt)).scalars().first()
    assert roadmap is not None
    
    stmt = select(RoadmapStage).where(RoadmapStage.roadmap_id == roadmap.id)
    stages = (await async_db.execute(stmt)).scalars().all()
    assert len(stages) >= 1
    assert str(stages[0].stage_type.value).upper() == "READINESS"
    
    # 3. Prerequisite Violation Check
    stage2 = await roadmap_svc.add_roadmap_stage(roadmap.id, "MARKET", 1)
    
    with pytest.raises(ValueError, match="Prerequisite stage not completed"):
        await roadmap_svc.transition_stage(stage2.id, RoadmapStageStatus.ACTIVE)

@pytest.mark.asyncio
async def test_billing_cross_module_enforcement(async_db: AsyncSession, test_user: User):
    """Verifies usage limits blocking AI operations."""
    roadmap_svc = BusinessRoadmapService(async_db)
    collab_svc = BusinessCollaboratorService(async_db)
    biz_svc = BusinessService(async_db, roadmap_svc, collab_svc)
    usage_svc = UsageService(async_db)
    ai_svc = AIService(async_db)
    
    # 1. Setup Business and Roadmap Stage
    bus_in = BusinessCreate(
        name="AI Corp", 
        owner_id=test_user.id, 
        stage=BusinessStage.EARLY
    )
    bus = await biz_svc.create_business(bus_in)
    
    stmt = select(BusinessRoadmap).where(BusinessRoadmap.business_id == bus.id)
    roadmap = (await async_db.execute(stmt)).scalars().first()
    
    stmt = select(RoadmapStage).where(RoadmapStage.roadmap_id == roadmap.id)
    stages = (await async_db.execute(stmt)).scalars().all()
    stage = stages[0]
    
    # 2. Set artificial limit to 0
    await usage_svc.record_usage(test_user.id, "AI_REQUEST", quantity=0)
    
    stmt = select(Usage).where(Usage.user_id == test_user.id, Usage.resource_type == "AI_REQUEST")
    usage = (await async_db.execute(stmt)).scalars().first()
    
    usage.limit_value = 0
    async_db.add(usage)
    await async_db.commit()
    
    # 3. Attempt AI run -> Should fail
    agent = await ai_svc.create_agent("SupremeBot", "RESEARCH", {})
    
    with pytest.raises(PermissionError, match="Insufficient AI quota"):
        # Correctly call the service instance method
        await ai_svc.initiate_agent_run(agent.id, test_user.id, test_user.id, "USER", stage_id=stage.id)

if __name__ == "__main__":
    pytest.main([__file__])
