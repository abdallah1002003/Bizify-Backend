from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.business.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.services.business.business_service import BusinessService, get_business_service
from app.core import dependencies
import app.models as models

router = APIRouter()

@router.get("/", response_model=List[BusinessResponse])
def read_businesses(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """List businesses owned by current user with pagination."""
    return service.get_businesses(skip=skip, limit=limit, owner_id=current_user.id)

@router.post("/", response_model=BusinessResponse)
def create_business(
    item_in: BusinessCreate, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Logic-injected creation (auto-roadmap/collaborator)."""
    item_in.owner_id = current_user.id or item_in.owner_id
    return service.create_business(obj_in=item_in)

@router.get("/{id}", response_model=BusinessResponse)
def read_business(
    id: UUID, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Secure retrieval."""
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    # Ownership Check
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return db_obj

@router.put("/{id}", response_model=BusinessResponse)
def update_business(
    id: UUID, item_in: BusinessUpdate, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Protected mutation."""
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ownership required")
    return service.update_business(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=BusinessResponse)
def delete_business(
    id: UUID, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Destructive operation guard."""
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Destructive admin rights required")
    return service.delete_business(id=id)
