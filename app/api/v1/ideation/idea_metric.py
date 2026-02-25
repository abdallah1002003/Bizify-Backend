from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea_metric import IdeaMetricCreate, IdeaMetricUpdate, IdeaMetricResponse
from app.services.ideation import idea_metric as service

router = APIRouter()

@router.get("/", response_model=List[IdeaMetricResponse])
def read_idea_metrics(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):  # type: ignore
    return service.get_idea_metrics(db, skip=skip, limit=limit)

@router.post("/", response_model=IdeaMetricResponse)
def create_idea_metric(item_in: IdeaMetricCreate, db: Session = Depends(get_db)):  # type: ignore
    return service.create_idea_metric(db, obj_in=item_in)

@router.get("/{id}", response_model=IdeaMetricResponse)
def read_idea_metric(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_idea_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return db_obj

@router.put("/{id}", response_model=IdeaMetricResponse)
def update_idea_metric(id: UUID, item_in: IdeaMetricUpdate, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_idea_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return service.update_idea_metric(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaMetricResponse)
def delete_idea_metric(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_idea_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaMetric not found")
    return service.delete_idea_metric(db, id=id)
