from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.partners.partner_profile import PartnerProfileCreate, PartnerProfileUpdate, PartnerProfileResponse
from app.services.partners import partner_service as service

router = APIRouter()

@router.get("/", response_model=List[PartnerProfileResponse])
async def read_partner_profiles(skip: SkipParam = 0, limit: LimitParam = 100, db: AsyncSession = Depends(get_async_db)):
    return await service.get_partner_profiles(db, skip=skip, limit=limit)

@router.post("/", response_model=PartnerProfileResponse)
async def create_partner_profile(item_in: PartnerProfileCreate, db: AsyncSession = Depends(get_async_db)):
    """Elite API: Registers a verified partner profile."""
    return await service.create_partner_profile(
        db, 
        user_id=item_in.user_id, 
        partner_type=item_in.partner_type, 
        bio=item_in.description or "", 
        details=item_in.services_json or {}
    )

@router.get("/{id}", response_model=PartnerProfileResponse)
async def read_partner_profile(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_partner_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return db_obj

@router.put("/{id}", response_model=PartnerProfileResponse)
async def update_partner_profile(id: UUID, item_in: PartnerProfileUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_partner_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return await service.update_partner_profile(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=PartnerProfileResponse)
async def delete_partner_profile(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_partner_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return await service.delete_partner_profile(db, id=id)
