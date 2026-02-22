from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user
from app.core.cache import cache
import app.models as models
from app.db.database import get_db
from app.models.enums import UserRole
from app.schemas.billing.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.billing import billing_service as service

router = APIRouter()


def _require_admin(current_user: models.User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")


@router.get("/", response_model=List[PlanResponse])
@cache(ttl_seconds=300)
def read_plans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    return service.get_plans(db, skip=skip, limit=limit)

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
