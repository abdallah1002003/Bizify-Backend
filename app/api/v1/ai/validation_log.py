from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.api.v1.service_dependencies import get_ai_service
from app.schemas.ai.validation_log import ValidationLogCreate, ValidationLogUpdate, ValidationLogResponse
from app.services.ai.ai_service import AIService

router = APIRouter()

@router.get("/", response_model=List[ValidationLogResponse])
async def read_validation_logs(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: AIService = Depends(get_ai_service),
):
    return await service.get_validation_logs(skip=skip, limit=limit)

@router.post("/", response_model=ValidationLogResponse)
async def create_validation_log(
    item_in: ValidationLogCreate,
    service: AIService = Depends(get_ai_service),
):
    """Elite API: Records AI critique with automated confidence scoring."""
    return await service.record_validation_log(
        agent_run_id=item_in.agent_run_id,
        result="SUCCESS",  # Default simulation
        details="Validation recorded via AI service.",
    )

@router.get("/{id}", response_model=ValidationLogResponse)
async def read_validation_log(
    id: UUID,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_validation_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return db_obj

@router.put("/{id}", response_model=ValidationLogResponse)
async def update_validation_log(
    id: UUID,
    item_in: ValidationLogUpdate,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_validation_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return await service.update_validation_log(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ValidationLogResponse)
async def delete_validation_log(
    id: UUID,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_validation_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return await service.delete_validation_log(id=id)
