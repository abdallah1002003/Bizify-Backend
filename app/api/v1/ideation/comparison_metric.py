from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.comparison_metric import ComparisonMetricCreate, ComparisonMetricUpdate, ComparisonMetricResponse
from app.services.ideation import idea_comparison_metric as service

router = APIRouter()

@router.get("/", response_model=List[ComparisonMetricResponse])
def read_comparison_metrics(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):  # type: ignore
    return service.get_comparison_metrics(db, skip=skip, limit=limit)

@router.post("/", response_model=ComparisonMetricResponse)
def create_comparison_metric(item_in: ComparisonMetricCreate, db: Session = Depends(get_db)):  # type: ignore
    return service.create_comparison_metric(db, obj_in=item_in)

@router.get("/{id}", response_model=ComparisonMetricResponse)
def read_comparison_metric(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_comparison_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return db_obj

@router.put("/{id}", response_model=ComparisonMetricResponse)
def update_comparison_metric(id: UUID, item_in: ComparisonMetricUpdate, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_comparison_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return service.update_comparison_metric(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ComparisonMetricResponse)
def delete_comparison_metric(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_comparison_metric(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ComparisonMetric not found")
    return service.delete_comparison_metric(db, id=id)
