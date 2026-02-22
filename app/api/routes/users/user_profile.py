from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.enums import UserRole
from app.schemas.users.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.services.users import user_service as service
from app.core.dependencies import get_current_active_user
import app.models as models

router = APIRouter()


def _require_admin(current_user: models.User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")


def _require_admin_or_owner(current_user: models.User, owner_id: UUID) -> None:
    if current_user.role == UserRole.ADMIN or current_user.id == owner_id:
        return
    raise HTTPException(status_code=403, detail="Access denied")

@router.get("/", response_model=List[UserProfileResponse])
def read_user_profiles(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _require_admin(current_user)
    return service.get_user_profiles(db, skip=skip, limit=limit)

@router.post("/", response_model=UserProfileResponse)
def create_user_profile(
    item_in: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _require_admin_or_owner(current_user, item_in.user_id)
    if current_user.role != UserRole.ADMIN:
        item_in.user_id = current_user.id
    return service.create_user_profile(db, obj_in=item_in)

@router.get("/{id}", response_model=UserProfileResponse)
def read_user_profile(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    _require_admin_or_owner(current_user, db_obj.user_id)
    return db_obj

@router.put("/{id}", response_model=UserProfileResponse)
def update_user_profile(
    id: UUID,
    item_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    _require_admin_or_owner(current_user, db_obj.user_id)
    if current_user.role != UserRole.ADMIN:
        item_in.user_id = db_obj.user_id
    return service.update_user_profile(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=UserProfileResponse)
def delete_user_profile(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    _require_admin_or_owner(current_user, db_obj.user_id)
    return service.delete_user_profile(db, id=id)
