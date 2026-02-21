from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.partners.partner_request import PartnerRequestCreate, PartnerRequestUpdate, PartnerRequestResponse
from app.services.partners import partner_service as service

router = APIRouter()

@router.get("/", response_model=List[PartnerRequestResponse])
def read_partner_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_partner_requests(db, skip=skip, limit=limit)

@router.post("/", response_model=PartnerRequestResponse)
def create_partner_request(item_in: PartnerRequestCreate, db: Session = Depends(get_db)):
    """Elite API: Submits a partnership request with business context."""
    return service.submit_partner_request(
        db, 
        business_id=item_in.business_id, 
        partner_id=item_in.partner_id, 
        request_type="COLLABORATION", # Default logic
        context="Automated request generated via Master Service."
    )

@router.get("/{id}", response_model=PartnerRequestResponse)
def read_partner_request(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_partner_request(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return db_obj

@router.put("/{id}", response_model=PartnerRequestResponse)
def update_partner_request(id: UUID, item_in: PartnerRequestUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_partner_request(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return service.update_partner_request(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=PartnerRequestResponse)
def delete_partner_request(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_partner_request(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PartnerRequest not found")
    return service.delete_partner_request(db, id=id)
