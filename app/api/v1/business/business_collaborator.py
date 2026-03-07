from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.business.business_collaborator import BusinessCollaboratorCreate, BusinessCollaboratorUpdate, BusinessCollaboratorResponse
<<<<<<< HEAD
from app.services.business.business_collaborator import BusinessCollaboratorService
from app.api.v1.service_dependencies import get_business_collaborator_service
=======
from app.services.business.business_collaborator import BusinessCollaboratorService, get_business_collaborator_service
>>>>>>> origin/main

router = APIRouter()

@router.get("/", response_model=List[BusinessCollaboratorResponse])
async def read_business_collaborators(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: BusinessCollaboratorService = Depends(get_business_collaborator_service)
):
    return await service.get_business_collaborators(skip=skip, limit=limit)

@router.post("/", response_model=BusinessCollaboratorResponse)
async def create_business_collaborator(
    item_in: BusinessCollaboratorCreate, 
    service: BusinessCollaboratorService = Depends(get_business_collaborator_service)
):
    return await service.create_business_collaborator(obj_in=item_in)

@router.get("/{id}", response_model=BusinessCollaboratorResponse)
async def read_business_collaborator(
    id: UUID, 
    service: BusinessCollaboratorService = Depends(get_business_collaborator_service)
):
    db_obj = await service.get_business_collaborator(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return db_obj

@router.put("/{id}", response_model=BusinessCollaboratorResponse)
async def update_business_collaborator(
    id: UUID, 
    item_in: BusinessCollaboratorUpdate, 
    service: BusinessCollaboratorService = Depends(get_business_collaborator_service)
):
    db_obj = await service.get_business_collaborator(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return await service.update_business_collaborator(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessCollaboratorResponse)
async def delete_business_collaborator(
    id: UUID, 
    service: BusinessCollaboratorService = Depends(get_business_collaborator_service)
):
    db_obj = await service.get_business_collaborator(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return await service.delete_business_collaborator(id=id)
