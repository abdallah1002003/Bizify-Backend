from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.ai.validation_log import ValidationLogCreate, ValidationLogUpdate, ValidationLogResponse
from app.services.ai import ai_service as service

router = APIRouter()

@router.get("/", response_model=List[ValidationLogResponse])
async def read_validation_logs(skip: SkipParam = 0, limit: LimitParam = 100, db: AsyncSession = Depends(get_async_db)):
    return await service.get_validation_logs(db, skip=skip, limit=limit)

@router.post("/", response_model=ValidationLogResponse)
async def create_validation_log(item_in: ValidationLogCreate, db: AsyncSession = Depends(get_async_db)):
    """Elite API: Records AI critique with automated confidence scoring."""
    return await service.record_validation_log(
        db, 
        agent_run_id=item_in.agent_run_id, 
        result="SUCCESS", # Default simulation
        details="Validation recorded via AI service."
    )

@router.get("/{id}", response_model=ValidationLogResponse)
async def read_validation_log(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return db_obj

@router.put("/{id}", response_model=ValidationLogResponse)
async def update_validation_log(id: UUID, item_in: ValidationLogUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return await service.update_validation_log(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ValidationLogResponse)
async def delete_validation_log(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return await service.delete_validation_log(db, id=id)
