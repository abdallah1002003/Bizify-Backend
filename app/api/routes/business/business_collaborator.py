from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business_collaborator import BusinessCollaboratorCreate, BusinessCollaboratorUpdate, BusinessCollaboratorResponse
from app.services.business import business_service as service

router = APIRouter()

@router.get("/", response_model=List[BusinessCollaboratorResponse])
def read_business_collaborators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_business_collaborators(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessCollaboratorResponse)
def create_business_collaborator(item_in: BusinessCollaboratorCreate, db: Session = Depends(get_db)):
    return service.create_business_collaborator(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessCollaboratorResponse)
def read_business_collaborator(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_collaborator(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return db_obj

@router.put("/{id}", response_model=BusinessCollaboratorResponse)
def update_business_collaborator(id: UUID, item_in: BusinessCollaboratorUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_business_collaborator(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return service.update_business_collaborator(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessCollaboratorResponse)
def delete_business_collaborator(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_collaborator(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessCollaborator not found")
    return service.delete_business_collaborator(db, id=id)
