from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai.agent import AgentCreate, AgentUpdate, AgentResponse
from app.core.dependencies import get_current_active_user
from app.services.ai import ai_service as service

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.get("/", response_model=List[AgentResponse])
def read_agents(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: Session = Depends(get_db)
):
    """List all AI agents with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Agent records
    """
    return service.get_agents(db, skip=skip, limit=limit)

@router.post("/", response_model=AgentResponse)
def create_agent(item_in: AgentCreate, db: Session = Depends(get_db)):  # type: ignore
    """
    **Notice:** This AI Route is currently using Mock Logic. Actual AI execution is pending integration.
    
    Elite API: Registers a new AI agent template with phase logic.
    """
    return service.create_agent(db, name=item_in.name, phase=item_in.phase, config={})

@router.get("/{id}", response_model=AgentResponse)
def read_agent(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_obj

@router.put("/{id}", response_model=AgentResponse)
def update_agent(id: UUID, item_in: AgentUpdate, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return service.update_agent(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=AgentResponse)
def delete_agent(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return service.delete_agent(db, id=id)
