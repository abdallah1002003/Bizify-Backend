from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business_roadmap import BusinessRoadmapCreate, BusinessRoadmapUpdate, BusinessRoadmapResponse
from app.services.business import business_roadmap as service

router = APIRouter()

@router.get("/", response_model=List[BusinessRoadmapResponse])
def read_business_roadmaps(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):
    return service.get_business_roadmaps(db, skip=skip, limit=limit)

@router.post("/", response_model=BusinessRoadmapResponse)
def create_business_roadmap(item_in: BusinessRoadmapCreate, db: Session = Depends(get_db)):
    return service.create_business_roadmap(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessRoadmapResponse)
def read_business_roadmap(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_roadmap(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessRoadmap not found")
    return db_obj

@router.put("/{id}", response_model=BusinessRoadmapResponse)
def update_business_roadmap(id: UUID, item_in: BusinessRoadmapUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_business_roadmap(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessRoadmap not found")
    return service.update_business_roadmap(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessRoadmapResponse)
def delete_business_roadmap(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_business_roadmap(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="BusinessRoadmap not found")
    return service.delete_business_roadmap(db, id=id)
