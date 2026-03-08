from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate, ExperimentResponse
from app.services.ideation.idea_experiment import IdeaExperimentService, get_idea_experiment_service

router = APIRouter()

@router.get("/", response_model=List[ExperimentResponse])
async def read_experiments(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: IdeaExperimentService = Depends(get_idea_experiment_service)
):
    return await service.get_experiments(skip=skip, limit=limit)

@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    item_in: ExperimentCreate, 
    service: IdeaExperimentService = Depends(get_idea_experiment_service)
):
    return await service.create_experiment(obj_in=item_in)

@router.get("/{id}", response_model=ExperimentResponse)
async def read_experiment(
    id: UUID, 
    service: IdeaExperimentService = Depends(get_idea_experiment_service)
):
    db_obj = await service.get_experiment(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_obj

@router.put("/{id}", response_model=ExperimentResponse)
async def update_experiment(
    id: UUID, 
    item_in: ExperimentUpdate, 
    service: IdeaExperimentService = Depends(get_idea_experiment_service)
):
    db_obj = await service.get_experiment(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await service.update_experiment(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ExperimentResponse)
async def delete_experiment(
    id: UUID, 
    service: IdeaExperimentService = Depends(get_idea_experiment_service)
):
    db_obj = await service.get_experiment(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await service.delete_experiment(id=id)
