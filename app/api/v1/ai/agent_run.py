from typing import List
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
<<<<<<< HEAD
from app.db.database import AsyncSessionLocal
from app.schemas.ai.agent_run import AgentRunCreate, AgentRunUpdate, AgentRunResponse
from app.core.dependencies import get_current_active_user
from app.api.v1.service_dependencies import get_ai_service, get_business_roadmap_service
from app.services.ai.ai_service import AIService
from app.services.business.business_roadmap import BusinessRoadmapService
=======
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db, AsyncSessionLocal
from app.schemas.ai.agent_run import AgentRunCreate, AgentRunUpdate, AgentRunResponse
from app.core.dependencies import get_current_active_user
from app.services.ai import ai_service as service
from app.services.business.business_roadmap import BusinessRoadmapService, get_business_roadmap_service
>>>>>>> origin/main
import app.models as models

router = APIRouter(dependencies=[Depends(get_current_active_user)])


<<<<<<< HEAD
async def _ensure_agent_run_owner(db_obj: models.AgentRun, current_user: models.User) -> None:
=======
async def _ensure_agent_run_owner(db: AsyncSession, db_obj: models.AgentRun, current_user: models.User) -> None:
>>>>>>> origin/main
    # In async, we might need to ensure relationships are loaded. 
    # For now, we assume the initial query or eager loading handled it, 
    # but more robust is to ensure it.
    stage = db_obj.stage
    business = stage.roadmap.business if stage and stage.roadmap else None
    if business is None:
        raise HTTPException(status_code=404, detail="AgentRun context not found")
    if business.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[AgentRunResponse])
async def read_agent_runs(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """List agent runs for current user's businesses with pagination."""
    return await service.get_agent_runs(skip=skip, limit=limit, user_id=current_user.id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """List agent runs for current user's businesses with pagination."""
    return await service.get_agent_runs(db, skip=skip, limit=limit, user_id=current_user.id)
>>>>>>> origin/main

@router.post("/", response_model=AgentRunResponse)
async def create_agent_run(
    item_in: AgentRunCreate, 
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
=======
    db: AsyncSession = Depends(get_async_db),
>>>>>>> origin/main
    roadmap_service: BusinessRoadmapService = Depends(get_business_roadmap_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elite API: Initiates an AI agent run with usage enforcement.
    """
    stage = await roadmap_service.get_roadmap_stage(item_in.stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    business = stage.roadmap.business
    if business.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    input_context = {
        "business_id": str(business.id),
        "idea_id": str(business.idea_id) if business.idea_id else None,
        "stage_type": stage.stage_type.value if hasattr(stage.stage_type, "value") else stage.stage_type,
        "business_context": business.context_json
    }

    return await service.initiate_agent_run(
<<<<<<< HEAD
        agent_id=item_in.agent_id,
        user_id=current_user.id,
        target_id=current_user.id,  # Default to user context
        target_type="USER",
        stage_id=item_in.stage_id,
        input_data=input_context,
=======
        db, 
        agent_id=item_in.agent_id, 
        user_id=current_user.id, 
        target_id=current_user.id, # Default to user context
        target_type="USER",
        stage_id=item_in.stage_id,
        input_data=input_context
>>>>>>> origin/main
    )

@router.get("/{id}", response_model=AgentRunResponse)
async def read_agent_run(
    id: UUID,
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db_obj, current_user)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db, db_obj, current_user)
>>>>>>> origin/main
    return db_obj

@router.put("/{id}", response_model=AgentRunResponse)
async def update_agent_run(
    id: UUID,
    item_in: AgentRunUpdate,
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db_obj, current_user)
    return await service.update_agent_run(db_obj=db_obj, obj_in=item_in)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db, db_obj, current_user)
    return await service.update_agent_run(db, db_obj=db_obj, obj_in=item_in)
>>>>>>> origin/main

@router.delete("/{id}", response_model=AgentRunResponse)
async def delete_agent_run(
    id: UUID,
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db_obj, current_user)
    return await service.delete_agent_run(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db, db_obj, current_user)
    return await service.delete_agent_run(db, id=id)
>>>>>>> origin/main

@router.post(
    "/{id}/execute",
    status_code=202,
    response_model=AgentRunResponse,
)
async def execute_agent_run(
    id: UUID,
    background_tasks: BackgroundTasks,
<<<<<<< HEAD
    service: AIService = Depends(get_ai_service),
=======
    db: AsyncSession = Depends(get_async_db),
>>>>>>> origin/main
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Queue an agent run for asynchronous execution.

    Returns **202 Accepted** immediately after the run is queued.
    """
<<<<<<< HEAD
    db_obj = await service.get_agent_run(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db_obj, current_user)

    # Use the async session maker for background tasks
    background_tasks.add_task(AIService.run_agent_in_background, AsyncSessionLocal, id)
=======
    db_obj = await service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    await _ensure_agent_run_owner(db, db_obj, current_user)

    # Use the async session maker for background tasks
    background_tasks.add_task(service.run_agent_in_background, AsyncSessionLocal, id)
>>>>>>> origin/main
    return db_obj
