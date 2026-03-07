from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.api.v1.service_dependencies import get_partner_request_service
from app.schemas.partners.partner_request import PartnerRequestCreate, PartnerRequestUpdate, PartnerRequestResponse
from app.services.partners.partner_request import PartnerRequestService

router = APIRouter()

@router.get("/", response_model=List[PartnerRequestResponse])
async def read_partner_requests(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: PartnerRequestService = Depends(get_partner_request_service),
):
    return await service.get_partner_requests(skip=skip, limit=limit)

@router.post("/", response_model=PartnerRequestResponse)
async def create_partner_request(
    item_in: PartnerRequestCreate,
    service: PartnerRequestService = Depends(get_partner_request_service),
):
    """Elite API: Submits a partnership request with business context."""
    return await service.submit_partner_request(
        business_id=item_in.business_id,
        partner_id=item_in.partner_id,
        request_type="COLLABORATION",  # Default logic
        context="Automated request generated via Master Service.",
    )

@router.get("/{id}", response_model=PartnerRequestResponse)
async def read_partner_request(
    id: UUID,
    service: PartnerRequestService = Depends(get_partner_request_service),
):
    db_obj = await service.get_partner_request(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return db_obj

@router.put("/{id}", response_model=PartnerRequestResponse)
async def update_partner_request(
    id: UUID,
    item_in: PartnerRequestUpdate,
    service: PartnerRequestService = Depends(get_partner_request_service),
):
    db_obj = await service.get_partner_request(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return await service.update_partner_request(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=PartnerRequestResponse)
async def delete_partner_request(
    id: UUID,
    service: PartnerRequestService = Depends(get_partner_request_service),
):
    db_obj = await service.get_partner_request(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return await service.delete_partner_request(id=id)
