from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user
import app.models as models
from app.models.billing.billing import Plan
from app.db.database import get_db
from app.models.enums import UserRole
from app.schemas.billing.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.billing import plan_service as service

router = APIRouter()


def _require_admin(current_user: models.User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")


@router.get("/", response_model=PageResponse[PlanResponse])
def read_plans(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all billing plans with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Plan records (PageResponse)
    """
    _ = current_user
    total = db.query(Plan).count()
    items = service.get_plans(db, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}

@router.post("/", response_model=PlanResponse)
def create_plan(
    item_in: PlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _require_admin(current_user)
    return service.create_plan(db, obj_in=item_in)

@router.get("/{id}", response_model=PlanResponse)
def read_plan(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = service.get_plan(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_obj

@router.put("/{id}", response_model=PlanResponse)
def update_plan(
    id: UUID,
    item_in: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _require_admin(current_user)
    db_obj = service.get_plan(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.update_plan(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=PlanResponse)
def delete_plan(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _require_admin(current_user)
    db_obj = service.get_plan(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.delete_plan(db, id=id)
