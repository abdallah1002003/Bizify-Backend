from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.api.v1.service_dependencies import get_partner_profile_service
from app.schemas.partners.partner_profile import PartnerProfileCreate, PartnerProfileUpdate, PartnerProfileResponse
from app.services.partners.partner_profile import PartnerProfileService

router = APIRouter()

@router.get("/", response_model=List[PartnerProfileResponse])
async def read_partner_profiles(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: PartnerProfileService = Depends(get_partner_profile_service),
):
    return await service.get_partner_profiles(skip=skip, limit=limit)

@router.post("/", response_model=PartnerProfileResponse)
async def create_partner_profile(
    item_in: PartnerProfileCreate,
    service: PartnerProfileService = Depends(get_partner_profile_service),
):
    """Elite API: Registers a verified partner profile."""
    return await service.create_partner_profile(
        user_id=item_in.user_id,
        partner_type=item_in.partner_type,
        bio=item_in.description or "",
        details=item_in.services_json or {},
    )

@router.get("/{id}", response_model=PartnerProfileResponse)
async def read_partner_profile(
    id: UUID,
    service: PartnerProfileService = Depends(get_partner_profile_service),
):
    db_obj = await service.get_partner_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return db_obj

@router.put("/{id}", response_model=PartnerProfileResponse)
async def update_partner_profile(
    id: UUID,
    item_in: PartnerProfileUpdate,
    service: PartnerProfileService = Depends(get_partner_profile_service),
):
    db_obj = await service.get_partner_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return await service.update_partner_profile(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=PartnerProfileResponse)
async def delete_partner_profile(
    id: UUID,
    service: PartnerProfileService = Depends(get_partner_profile_service),
):
    db_obj = await service.get_partner_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerProfile not found")
    return await service.delete_partner_profile(id=id)
