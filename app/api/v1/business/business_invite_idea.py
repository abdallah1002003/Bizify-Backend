# type: ignore
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business_invite_idea import BusinessInviteIdeaCreate, BusinessInviteIdeaUpdate, BusinessInviteIdeaResponse
from app.services.business import business_invite as service

router = APIRouter()

@router.get("/", response_model=List[BusinessInviteIdeaResponse])
def read_business_invite_ideas(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_business_invite_ideas(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessInviteIdeaResponse)
def create_business_invite_idea(item_in: BusinessInviteIdeaCreate, db: Session = Depends(get_db)):
    return service.create_business_invite_idea(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessInviteIdeaResponse)
def read_business_invite_idea(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite_idea(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return db_obj

@router.put("/{id}", response_model=BusinessInviteIdeaResponse)
def update_business_invite_idea(id: UUID, item_in: BusinessInviteIdeaUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite_idea(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return service.update_business_invite_idea(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessInviteIdeaResponse)
def delete_business_invite_idea(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_invite_idea(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessInviteIdea not found")
    return service.delete_business_invite_idea(db, id=id)
