from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.business.roadmap_stage import RoadmapStageCreate, RoadmapStageUpdate, RoadmapStageResponse
from app.services.business.business_roadmap import BusinessRoadmapService, get_business_roadmap_service

router = APIRouter()

@router.get("/", response_model=List[RoadmapStageResponse])
async def read_roadmap_stages(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: BusinessRoadmapService = Depends(get_business_roadmap_service)
):
    return await service.get_roadmap_stages(skip=skip, limit=limit)

@router.post("/", response_model=RoadmapStageResponse)
async def create_roadmap_stage(
    item_in: RoadmapStageCreate, 
    service: BusinessRoadmapService = Depends(get_business_roadmap_service)
):
    return await service.create_roadmap_stage(obj_in=item_in)

@router.get("/{id}", response_model=RoadmapStageResponse)
async def read_roadmap_stage(
    id: UUID, 
    service: BusinessRoadmapService = Depends(get_business_roadmap_service)
):
    db_obj = await service.get_roadmap_stage(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return db_obj

@router.put("/{id}", response_model=RoadmapStageResponse)
async def update_roadmap_stage(
    id: UUID, 
    item_in: RoadmapStageUpdate, 
    service: BusinessRoadmapService = Depends(get_business_roadmap_service)
):
    db_obj = await service.get_roadmap_stage(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return await service.update_roadmap_stage(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=RoadmapStageResponse)
async def delete_roadmap_stage(
    id: UUID, 
    service: BusinessRoadmapService = Depends(get_business_roadmap_service)
):
    db_obj = await service.get_roadmap_stage(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return await service.delete_roadmap_stage(id=id)
