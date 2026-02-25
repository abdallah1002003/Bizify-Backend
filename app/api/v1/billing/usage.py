from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.billing.usage import UsageCreate, UsageUpdate, UsageResponse
from app.services.billing import usage_service as service

router = APIRouter()


def _ensure_usage_owner(usage: models.Usage, current_user: models.User) -> None:
    if usage.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[UsageResponse])
def read_usages(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return service.get_usages(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=UsageResponse)
def create_usage(  # type: ignore
    item_in: UsageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return service.create_usage(db, obj_in=data)

@router.get("/{id}", response_model=UsageResponse)
def read_usage(  # type: ignore
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_usage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=UsageResponse)
def update_usage(  # type: ignore
    id: UUID,
    item_in: UsageUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_usage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return service.update_usage(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=UsageResponse)
def delete_usage(  # type: ignore
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_usage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    return service.delete_usage(db, id=id)
