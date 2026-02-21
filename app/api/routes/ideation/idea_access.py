from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea_access import IdeaAccessCreate, IdeaAccessUpdate, IdeaAccessResponse
from app.services.ideation import idea_service as service

router = APIRouter()

@router.get("/", response_model=List[IdeaAccessResponse])
def read_idea_accesss(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_idea_accesss(db, skip=skip, limit=limit)

@router.post("/", response_model=IdeaAccessResponse)
def create_idea_access(item_in: IdeaAccessCreate, db: Session = Depends(get_db)):
    return service.create_idea_access(db, obj_in=item_in)

@router.get("/{id}", response_model=IdeaAccessResponse)
def read_idea_access(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    return db_obj

@router.put("/{id}", response_model=IdeaAccessResponse)
def update_idea_access(id: UUID, item_in: IdeaAccessUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    return service.update_idea_access(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaAccessResponse)
def delete_idea_access(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    return service.delete_idea_access(db, id=id)
