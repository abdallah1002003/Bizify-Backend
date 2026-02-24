from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, require_admin
import app.models as models
from app.models.billing.billing import Plan
from app.db.database import get_db
from app.schemas.billing.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.billing import plan_service as service

router = APIRouter()


@router.get("/", response_model=PageResponse[PlanResponse])
def read_plans(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all billing plans with pagination. Accessible to all authenticated users."""
    _ = current_user
    total = db.query(Plan).count()
    items = service.get_plans(db, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def create_plan(
    item_in: PlanCreate,
    db: Session = Depends(get_db),
):
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


@router.put("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def update_plan(
    id: UUID,
    item_in: PlanUpdate,
    db: Session = Depends(get_db),
):
    db_obj = service.get_plan(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.update_plan(db, db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def delete_plan(
    id: UUID,
    db: Session = Depends(get_db),
):
    db_obj = service.get_plan(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.delete_plan(db, id=id)
