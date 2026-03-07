from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
<<<<<<< HEAD
from app.api.v1.service_dependencies import get_business_invite_service
from app.schemas.business.business_invite_idea import BusinessInviteIdeaCreate, BusinessInviteIdeaUpdate, BusinessInviteIdeaResponse
from app.services.business.business_invite import BusinessInviteService
=======
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.business.business_invite_idea import BusinessInviteIdeaCreate, BusinessInviteIdeaUpdate, BusinessInviteIdeaResponse
from app.services.business import business_invite as service
>>>>>>> origin/main

router = APIRouter()

@router.get("/", response_model=List[BusinessInviteIdeaResponse])
<<<<<<< HEAD
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
=======
async def read_business_invite_ideas(skip: SkipParam = 0, limit: LimitParam = 100, db: AsyncSession = Depends(get_async_db)):
    return await service.get_business_invite_ideas(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteIdeaResponse)
async def create_business_invite_idea(item_in: BusinessInviteIdeaCreate, db: AsyncSession = Depends(get_async_db)):
    return await service.create_business_invite_idea(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteIdeaResponse)
async def read_business_invite_idea(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite_idea(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return db_obj

@router.put("/{id}", response_model=BusinessInviteIdeaResponse)
<<<<<<< HEAD
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
=======
async def update_business_invite_idea(id: UUID, item_in: BusinessInviteIdeaUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite_idea(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return await service.update_business_invite_idea(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteIdeaResponse)
async def delete_business_invite_idea(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite_idea(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return await service.delete_business_invite_idea(db, id=id)
>>>>>>> origin/main
