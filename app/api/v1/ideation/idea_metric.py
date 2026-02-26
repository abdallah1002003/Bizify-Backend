from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.idea_metric import IdeaMetricCreate, IdeaMetricUpdate, IdeaMetricResponse
from app.services.ideation.idea_metric import IdeaMetricService, get_idea_metric_service

router = APIRouter()

@router.get("/", response_model=List[IdeaMetricResponse])
async def read_idea_metrics(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: IdeaMetricService = Depends(get_idea_metric_service)
):
    return await service.get_idea_metrics(skip=skip, limit=limit)

@router.post("/", response_model=IdeaMetricResponse)
async def create_idea_metric(
    item_in: IdeaMetricCreate, 
    service: IdeaMetricService = Depends(get_idea_metric_service)
):
    return await service.create_idea_metric(obj_in=item_in)

@router.get("/{id}", response_model=IdeaMetricResponse)
async def read_idea_metric(
    id: UUID, 
    service: IdeaMetricService = Depends(get_idea_metric_service)
):
    db_obj = await service.get_idea_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return db_obj

@router.put("/{id}", response_model=IdeaMetricResponse)
async def update_idea_metric(
    id: UUID, 
    item_in: IdeaMetricUpdate, 
    service: IdeaMetricService = Depends(get_idea_metric_service)
):
    db_obj = await service.get_idea_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return await service.update_idea_metric(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaMetricResponse)
async def delete_idea_metric(
    id: UUID, 
    service: IdeaMetricService = Depends(get_idea_metric_service)
):
    db_obj = await service.get_idea_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return await service.delete_idea_metric(id=id)
