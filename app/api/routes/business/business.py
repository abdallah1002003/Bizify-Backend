from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.services.business import business_core as service
from app.core import dependencies
import app.models as models

router = APIRouter()

@router.get("/", response_model=List[BusinessResponse])
def read_businesses(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """List businesses owned by current user with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Business records owned by the authenticated user
    """
    skip = max(0, skip)
    limit = max(1, min(limit, 100))
    return service.get_businesses(db, skip=skip, limit=limit, owner_id=current_user.id)

@router.post("/", response_model=BusinessResponse)
def create_business(
    item_in: BusinessCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Logic-injected creation (auto-roadmap/collaborator)."""
    item_in.owner_id = current_user.id or item_in.owner_id
    return service.create_business(db, obj_in=item_in)

@router.get("/{id}", response_model=BusinessResponse)
def read_business(
    id: UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Secure retrieval."""
    db_obj = service.get_business(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    # Ownership Check
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return db_obj

@router.put("/{id}", response_model=BusinessResponse)
def update_business(
    id: UUID, item_in: BusinessUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Protected mutation."""
    db_obj = service.get_business(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ownership required")
    return service.update_business(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessResponse)
def delete_business(
    id: UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Destructive operation guard."""
    db_obj = service.get_business(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Destructive admin rights required")
    return service.delete_business(db, id=id)
