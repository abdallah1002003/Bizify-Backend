from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea_comparison import IdeaComparisonCreate, IdeaComparisonUpdate, IdeaComparisonResponse
from app.services.ideation import idea_comparison as service

router = APIRouter()

@router.get("/", response_model=List[IdeaComparisonResponse])
def read_idea_comparisons(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_idea_comparisons(db, skip=skip, limit=limit)

@router.post("/", response_model=IdeaComparisonResponse)
def create_idea_comparison(item_in: IdeaComparisonCreate, db: Session = Depends(get_db)):
    return service.create_idea_comparison(db, obj_in=item_in)

@router.get("/{id}", response_model=IdeaComparisonResponse)
def read_idea_comparison(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_comparison(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return db_obj

@router.put("/{id}", response_model=IdeaComparisonResponse)
def update_idea_comparison(id: UUID, item_in: IdeaComparisonUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_idea_comparison(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return service.update_idea_comparison(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaComparisonResponse)
def delete_idea_comparison(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_idea_comparison(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaComparison not found")
    return service.delete_idea_comparison(db, id=id)
