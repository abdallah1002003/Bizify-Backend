from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.api.v1.service_dependencies import get_business_invite_service
from app.schemas.business.business_invite_idea import BusinessInviteIdeaCreate, BusinessInviteIdeaUpdate, BusinessInviteIdeaResponse
from app.services.business.business_invite import BusinessInviteService

router = APIRouter()

@router.get("/", response_model=List[BusinessInviteIdeaResponse])
async def read_business_invite_ideas(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    return await service.get_business_invite_ideas(skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteIdeaResponse)
async def create_business_invite_idea(
    item_in: BusinessInviteIdeaCreate,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    return await service.create_business_invite_idea(obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteIdeaResponse)
async def read_business_invite_idea(
    id: UUID,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite_idea(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return db_obj

@router.put("/{id}", response_model=BusinessInviteIdeaResponse)
async def update_business_invite_idea(
    id: UUID,
    item_in: BusinessInviteIdeaUpdate,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite_idea(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return await service.update_business_invite_idea(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteIdeaResponse)
async def delete_business_invite_idea(
    id: UUID,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite_idea(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return await service.delete_business_invite_idea(id=id)
