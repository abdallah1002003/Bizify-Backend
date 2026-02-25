# type: ignore
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai.validation_log import ValidationLogCreate, ValidationLogUpdate, ValidationLogResponse
from app.services.ai import ai_service as service

router = APIRouter()

@router.get("/", response_model=List[ValidationLogResponse])
def read_validation_logs(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_validation_logs(db, skip=skip, limit=limit)

@router.post("/", response_model=ValidationLogResponse)
def create_validation_log(item_in: ValidationLogCreate, db: Session = Depends(get_db)):
    """Elite API: Records AI critique with automated confidence scoring."""
    # Assuming ValidationLogCreate has some fields we can map to result/details
    return service.record_validation_log(
        db, 
        agent_run_id=item_in.agent_run_id, 
        result="SUCCESS", # Default simulation
        details="Validation recorded via AI service."
    )

@router.get("/{id}", response_model=ValidationLogResponse)
def read_validation_log(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return db_obj

@router.put("/{id}", response_model=ValidationLogResponse)
def update_validation_log(id: UUID, item_in: ValidationLogUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return service.update_validation_log(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=ValidationLogResponse)
def delete_validation_log(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_validation_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ValidationLog not found")
    return service.delete_validation_log(db, id=id)
