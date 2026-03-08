import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ideation.idea_experiment import IdeaExperimentService
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate
from app.models.enums import ExperimentStatus, IdeaStatus
import app.models as models

@pytest_asyncio.fixture
async def experiment_service(async_db: AsyncSession):
    return IdeaExperimentService(async_db)

@pytest.mark.asyncio
async def test_create_experiment(experiment_service, async_db):
    idea_id = uuid4()
    creator_id = uuid4()
    
    # Mocking idea access would be better, but let's just test CRUD first
    obj_in = ExperimentCreate(
        idea_id=idea_id,
        created_by=creator_id,
        hypothesis="Test hypothesis",
        status=ExperimentStatus.RUNNING,
        result_summary={}
    )
    exp = await experiment_service.create_experiment(obj_in)
    
    assert exp.hypothesis == "Test hypothesis"
    assert exp.status == ExperimentStatus.RUNNING

@pytest.mark.asyncio
async def test_update_experiment(experiment_service, async_db):
    idea_id = uuid4()
    creator_id = uuid4()
    exp = await experiment_service.create_experiment(ExperimentCreate(
        idea_id=idea_id,
        created_by=creator_id,
        hypothesis="Initial",
        status=ExperimentStatus.RUNNING,
        result_summary={}
    ))
    
    updated = await experiment_service.update_experiment(exp, ExperimentUpdate(hypothesis="Updated"))
    assert updated.hypothesis == "Updated"

@pytest.mark.asyncio
async def test_finalize_experiment_validates_idea(experiment_service, async_db):
    # Setup idea
    user = models.User(
        email=f"u-{uuid4()}@test.com", 
        password_hash="hash", 
        name="User",
        role=models.enums.UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True
    )
    async_db.add(user)
    await async_db.flush()
    
    idea = models.Idea(owner_id=user.id, title="Test Idea", description="Desc", status=IdeaStatus.DRAFT)
    async_db.add(idea)
    await async_db.flush()
    
    exp = await experiment_service.create_experiment(ExperimentCreate(
        idea_id=idea.id,
        created_by=user.id,
        hypothesis="H",
        status=ExperimentStatus.RUNNING,
        result_summary={}
    ))
    
    # Finalize
    await experiment_service.finalize_experiment(exp.id, {"win": True}, ExperimentStatus.COMPLETED)
    
    await async_db.refresh(idea)
    assert idea.status == IdeaStatus.VALIDATED
