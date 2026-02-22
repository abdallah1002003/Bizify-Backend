from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.comparison_item import ComparisonItemCreate, ComparisonItemUpdate, ComparisonItemResponse
from app.services.ideation import idea_comparison_item as service

router = APIRouter()

@router.get("/", response_model=List[ComparisonItemResponse])
def read_comparison_items(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_comparison_items(db, skip=skip, limit=limit)

@router.post("/", response_model=ComparisonItemResponse)
def create_comparison_item(item_in: ComparisonItemCreate, db: Session = Depends(get_db)):
    return service.create_comparison_item(db, obj_in=item_in)

@router.get("/{id}", response_model=ComparisonItemResponse)
def read_comparison_item(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_comparison_item(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return db_obj

@router.put("/{id}", response_model=ComparisonItemResponse)
def update_comparison_item(id: UUID, item_in: ComparisonItemUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_comparison_item(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return service.update_comparison_item(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ComparisonItemResponse)
def delete_comparison_item(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_comparison_item(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonItem not found")
    return service.delete_comparison_item(db, id=id)
