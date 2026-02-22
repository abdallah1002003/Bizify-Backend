from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea_version import IdeaVersionCreate, IdeaVersionUpdate, IdeaVersionResponse
from app.services.ideation import idea_version as service

router = APIRouter()

@router.get("/", response_model=List[IdeaVersionResponse])
def read_idea_versions(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_idea_versions(db, skip=skip, limit=limit)

@router.post("/", response_model=IdeaVersionResponse)
def create_idea_version(item_in: IdeaVersionCreate, db: Session = Depends(get_db)):
    return service.create_idea_version(db, obj_in=item_in)

@router.get("/{id}", response_model=IdeaVersionResponse)
def read_idea_version(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_version(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return db_obj

@router.put("/{id}", response_model=IdeaVersionResponse)
def update_idea_version(id: UUID, item_in: IdeaVersionUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_idea_version(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return service.update_idea_version(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaVersionResponse)
def delete_idea_version(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_version(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaVersion not found")
    return service.delete_idea_version(db, id=id)
