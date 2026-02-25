from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business_invite import BusinessInviteCreate, BusinessInviteUpdate, BusinessInviteResponse
from app.services.business import business_invite as service

router = APIRouter()

@router.get("/", response_model=List[BusinessInviteResponse])
def read_business_invites(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_business_invites(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteResponse)
def create_business_invite(item_in: BusinessInviteCreate, db: Session = Depends(get_db)):
    return service.create_business_invite(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteResponse)
def read_business_invite(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return db_obj

@router.put("/{id}", response_model=BusinessInviteResponse)
def update_business_invite(id: UUID, item_in: BusinessInviteUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return service.update_business_invite(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteResponse)
def delete_business_invite(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInvite not found")
    return service.delete_business_invite(db, id=id)
