from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
<<<<<<< HEAD
from app.api.v1.service_dependencies import get_business_invite_service
from app.schemas.business.business_invite import BusinessInviteCreate, BusinessInviteUpdate, BusinessInviteResponse
from app.services.business.business_invite import BusinessInviteService
=======
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.business.business_invite import BusinessInviteCreate, BusinessInviteUpdate, BusinessInviteResponse
from app.services.business import business_invite as service
>>>>>>> origin/main

router = APIRouter()

@router.get("/", response_model=List[BusinessInviteResponse])
<<<<<<< HEAD
async def read_business_invites(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    return await service.get_business_invites(skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteResponse)
async def create_business_invite(
    item_in: BusinessInviteCreate,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    return await service.create_business_invite(obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteResponse)
async def read_business_invite(
    id: UUID,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite(id=id)
=======
async def read_business_invites(skip: SkipParam = 0, limit: LimitParam = 100, db: AsyncSession = Depends(get_async_db)):
    return await service.get_business_invites(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteResponse)
async def create_business_invite(item_in: BusinessInviteCreate, db: AsyncSession = Depends(get_async_db)):
    return await service.create_business_invite(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteResponse)
async def read_business_invite(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return db_obj

@router.put("/{id}", response_model=BusinessInviteResponse)
<<<<<<< HEAD
async def update_business_invite(
    id: UUID,
    item_in: BusinessInviteUpdate,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return await service.update_business_invite(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteResponse)
async def delete_business_invite(
    id: UUID,
    service: BusinessInviteService = Depends(get_business_invite_service),
):
    db_obj = await service.get_business_invite(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return await service.delete_business_invite(id=id)
=======
async def update_business_invite(id: UUID, item_in: BusinessInviteUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return await service.update_business_invite(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteResponse)
async def delete_business_invite(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_business_invite(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return await service.delete_business_invite(db, id=id)
>>>>>>> origin/main
