from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from app.schemas.users.user import UserCreate, UserUpdate, UserResponse
from app.services.users.user_service import UserService, get_user_service
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_admin_or_self,
)
import app.models as models
from app.models.users.user import User

router = APIRouter()


@router.get("/", response_model=PageResponse[UserResponse], dependencies=[Depends(require_admin)])
def read_users(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: UserService = Depends(get_user_service),
):
    total = service.db.query(User).count()
    items = service.get_users(skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=UserResponse)
def create_user(  # type: ignore
    item_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    data = item_in.model_dump()
    data["is_active"] = True
    data["is_verified"] = False
    return service.create_user(obj_in=data)


@router.get("/me", response_model=UserResponse)
def read_current_user(  # type: ignore
    current_user: models.User = Depends(get_current_active_user),
):
    return current_user


@router.get("/{id}", response_model=UserResponse)
def read_user(  # type: ignore
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return db_obj


@router.put("/{id}", response_model=UserResponse)
def update_user(  # type: ignore
    id: UUID,
    item_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return service.update_user(db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=UserResponse)
def delete_user(  # type: ignore
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return service.delete_user(id=id)


@router.post("/{id}/verify", response_model=UserResponse, dependencies=[Depends(require_admin)])
def verify_user(  # type: ignore
    id: UUID,
    service: UserService = Depends(get_user_service),
):
    """Manually verify a user's email (Admin only)."""
    db_obj = service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return service.update_user(db_obj=db_obj, obj_in={"is_verified": True})
