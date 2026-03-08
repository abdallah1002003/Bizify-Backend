from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.comparison_metric import ComparisonMetricCreate, ComparisonMetricUpdate, ComparisonMetricResponse
from app.services.ideation.idea_comparison_metric import ComparisonMetricService, get_comparison_metric_service

router = APIRouter()

@router.get("/", response_model=List[ComparisonMetricResponse])
async def read_comparison_metrics(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: ComparisonMetricService = Depends(get_comparison_metric_service)
):
    return await service.get_comparison_metrics(skip=skip, limit=limit)

@router.post("/", response_model=ComparisonMetricResponse)
async def create_comparison_metric(
    item_in: ComparisonMetricCreate, 
    service: ComparisonMetricService = Depends(get_comparison_metric_service)
):
    return await service.create_comparison_metric(obj_in=item_in)

@router.get("/{id}", response_model=ComparisonMetricResponse)
async def read_comparison_metric(
    id: UUID, 
    service: ComparisonMetricService = Depends(get_comparison_metric_service)
):
    db_obj = await service.get_comparison_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return db_obj

@router.put("/{id}", response_model=ComparisonMetricResponse)
async def update_comparison_metric(
    id: UUID, 
    item_in: ComparisonMetricUpdate, 
    service: ComparisonMetricService = Depends(get_comparison_metric_service)
):
    db_obj = await service.get_comparison_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return await service.update_comparison_metric(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ComparisonMetricResponse)
async def delete_comparison_metric(
    id: UUID, 
    service: ComparisonMetricService = Depends(get_comparison_metric_service)
):
    db_obj = await service.get_comparison_metric(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return await service.delete_comparison_metric(id=id)
