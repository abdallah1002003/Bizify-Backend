from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.roadmap_stage import RoadmapStageCreate, RoadmapStageUpdate, RoadmapStageResponse
from app.services.business import business_service as service

router = APIRouter()

@router.get("/", response_model=List[RoadmapStageResponse])
def read_roadmap_stages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_roadmap_stages(db, skip=skip, limit=limit)

@router.post("/", response_model=RoadmapStageResponse)
def create_roadmap_stage(item_in: RoadmapStageCreate, db: Session = Depends(get_db)):
    return service.create_roadmap_stage(db, obj_in=item_in)

@router.get("/{id}", response_model=RoadmapStageResponse)
def read_roadmap_stage(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_roadmap_stage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return db_obj

@router.put("/{id}", response_model=RoadmapStageResponse)
def update_roadmap_stage(id: UUID, item_in: RoadmapStageUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_roadmap_stage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return service.update_roadmap_stage(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=RoadmapStageResponse)
def delete_roadmap_stage(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_roadmap_stage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="RoadmapStage not found")
    return service.delete_roadmap_stage(db, id=id)
