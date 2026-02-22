from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.experiment import ExperimentCreate, ExperimentUpdate, ExperimentResponse
from app.services.ideation import idea_experiment as service

router = APIRouter()

@router.get("/", response_model=List[ExperimentResponse])
def read_experiments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_experiments(db, skip=skip, limit=limit)

@router.post("/", response_model=ExperimentResponse)
def create_experiment(item_in: ExperimentCreate, db: Session = Depends(get_db)):
    return service.create_experiment(db, obj_in=item_in)

@router.get("/{id}", response_model=ExperimentResponse)
def read_experiment(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_experiment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_obj

@router.put("/{id}", response_model=ExperimentResponse)
def update_experiment(id: UUID, item_in: ExperimentUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_experiment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return service.update_experiment(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ExperimentResponse)
def delete_experiment(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_experiment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return service.delete_experiment(db, id=id)
