# type: ignore
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.idea_version import IdeaVersionCreate, IdeaVersionUpdate, IdeaVersionResponse
from app.services.ideation.idea_version import IdeaVersionService, get_idea_version_service

router = APIRouter()

@router.get("/", response_model=List[IdeaVersionResponse])
def read_idea_versions(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: IdeaVersionService = Depends(get_idea_version_service)
):
    return service.get_idea_versions(skip=skip, limit=limit)

@router.post("/", response_model=IdeaVersionResponse)
def create_idea_version(
    item_in: IdeaVersionCreate, 
    service: IdeaVersionService = Depends(get_idea_version_service)
):
    return service.create_idea_version(obj_in=item_in)

@router.get("/{id}", response_model=IdeaVersionResponse)
def read_idea_version(
    id: UUID, 
    service: IdeaVersionService = Depends(get_idea_version_service)
):
    db_obj = service.get_idea_version(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return db_obj

@router.put("/{id}", response_model=IdeaVersionResponse)
def update_idea_version(
    id: UUID, 
    item_in: IdeaVersionUpdate, 
    service: IdeaVersionService = Depends(get_idea_version_service)
):
    db_obj = service.get_idea_version(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return service.update_idea_version(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaVersionResponse)
def delete_idea_version(
    id: UUID, 
    service: IdeaVersionService = Depends(get_idea_version_service)
):
    db_obj = service.get_idea_version(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return service.delete_idea_version(id=id)
