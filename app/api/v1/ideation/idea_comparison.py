from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.idea_comparison import IdeaComparisonCreate, IdeaComparisonUpdate, IdeaComparisonResponse
<<<<<<< HEAD
from app.services.ideation.idea_comparison import IdeaComparisonService
from app.api.v1.service_dependencies import get_idea_comparison_service
=======
from app.services.ideation.idea_comparison import IdeaComparisonService, get_idea_comparison_service
>>>>>>> origin/main

router = APIRouter()

@router.get("/", response_model=List[IdeaComparisonResponse])
async def read_idea_comparisons(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: IdeaComparisonService = Depends(get_idea_comparison_service)
):
    return await service.get_idea_comparisons(skip=skip, limit=limit)

@router.post("/", response_model=IdeaComparisonResponse)
async def create_idea_comparison(
    item_in: IdeaComparisonCreate, 
    service: IdeaComparisonService = Depends(get_idea_comparison_service)
):
    return await service.create_idea_comparison(obj_in=item_in)

@router.get("/{id}", response_model=IdeaComparisonResponse)
async def read_idea_comparison(
    id: UUID, 
    service: IdeaComparisonService = Depends(get_idea_comparison_service)
):
    db_obj = await service.get_idea_comparison(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return db_obj

@router.put("/{id}", response_model=IdeaComparisonResponse)
async def update_idea_comparison(
    id: UUID, 
    item_in: IdeaComparisonUpdate, 
    service: IdeaComparisonService = Depends(get_idea_comparison_service)
):
    db_obj = await service.get_idea_comparison(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return await service.update_idea_comparison(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaComparisonResponse)
async def delete_idea_comparison(
    id: UUID, 
    service: IdeaComparisonService = Depends(get_idea_comparison_service)
):
    db_obj = await service.get_idea_comparison(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return await service.delete_idea_comparison(id=id)
