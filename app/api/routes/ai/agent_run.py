from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai.agent_run import AgentRunCreate, AgentRunUpdate, AgentRunResponse
from app.core.dependencies import get_current_active_user
from app.services.ai import ai_service as service
import app.models as models

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.get("/", response_model=List[AgentRunResponse])
def read_agent_runs(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return service.get_agent_runs(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=AgentRunResponse)
def create_agent_run(
    item_in: AgentRunCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    **Notice:** This AI Route is currently using Mock Logic. Actual AI execution is pending integration.
    
    Elite API: Initiates an AI agent run with usage enforcement.
    """
    from app.models.business.business import RoadmapStage
    stage = db.query(RoadmapStage).filter(RoadmapStage.id == item_in.stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
        
    business = stage.roadmap.business
    input_context = {
        "business_id": str(business.id),
        "idea_id": str(business.idea_id) if business.idea_id else None,
        "stage_type": stage.stage_type.value if hasattr(stage.stage_type, "value") else stage.stage_type,
        "business_context": business.context_json
    }

    return service.initiate_agent_run(
        db, 
        agent_id=item_in.agent_id, 
        user_id=current_user.id, 
        target_id=current_user.id, # Default to user context
        target_type="USER",
        stage_id=item_in.stage_id,
        input_data=input_context
    )

@router.get("/{id}", response_model=AgentRunResponse)
def read_agent_run(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    return db_obj

@router.put("/{id}", response_model=AgentRunResponse)
def update_agent_run(id: UUID, item_in: AgentRunUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    return service.update_agent_run(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=AgentRunResponse)
def delete_agent_run(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_agent_run(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    return service.delete_agent_run(db, id=id)
