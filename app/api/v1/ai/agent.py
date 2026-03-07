from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.ai.agent import AgentCreate, AgentUpdate, AgentResponse
from app.core.dependencies import get_current_active_user
from app.services.ai import ai_service as service

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.get("/", response_model=List[AgentResponse])
async def read_agents(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: AsyncSession = Depends(get_async_db)
):
    """List all AI agents with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Agent records
    """
    return await service.get_agents(db, skip=skip, limit=limit)

@router.post("/", response_model=AgentResponse)
async def create_agent(item_in: AgentCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Elite API: Registers a new AI agent template with phase logic.
    """
    return await service.create_agent(db, name=item_in.name, phase=item_in.phase, config={})

@router.get("/{id}", response_model=AgentResponse)
async def read_agent(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_obj

@router.put("/{id}", response_model=AgentResponse)
async def update_agent(id: UUID, item_in: AgentUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await service.update_agent(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=AgentResponse)
async def delete_agent(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_agent(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await service.delete_agent(db, id=id)
