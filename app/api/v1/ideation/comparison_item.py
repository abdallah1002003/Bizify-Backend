from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.comparison_item import ComparisonItemCreate, ComparisonItemUpdate, ComparisonItemResponse
from app.services.ideation.idea_comparison_item import ComparisonItemService
from app.api.v1.service_dependencies import get_comparison_item_service

router = APIRouter()

@router.get("/", response_model=List[ComparisonItemResponse])
async def read_comparison_items(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: ComparisonItemService = Depends(get_comparison_item_service)
):
    return await service.get_comparison_items(skip=skip, limit=limit)

@router.post("/", response_model=ComparisonItemResponse)
async def create_comparison_item(
    item_in: ComparisonItemCreate, 
    service: ComparisonItemService = Depends(get_comparison_item_service)
):
    return await service.create_comparison_item(obj_in=item_in)

@router.get("/{id}", response_model=ComparisonItemResponse)
async def read_comparison_item(
    id: UUID, 
    service: ComparisonItemService = Depends(get_comparison_item_service)
):
    db_obj = await service.get_comparison_item(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return db_obj

@router.put("/{id}", response_model=ComparisonItemResponse)
async def update_comparison_item(
    id: UUID, 
    item_in: ComparisonItemUpdate, 
    service: ComparisonItemService = Depends(get_comparison_item_service)
):
    db_obj = await service.get_comparison_item(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return await service.update_comparison_item(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ComparisonItemResponse)
async def delete_comparison_item(
    id: UUID, 
    service: ComparisonItemService = Depends(get_comparison_item_service)
):
    db_obj = await service.get_comparison_item(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return await service.delete_comparison_item(id=id)
