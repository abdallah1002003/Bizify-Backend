from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from app.schemas.users.user import UserCreate, UserUpdate, UserResponse
from app.services.users.user_service import UserService
from app.api.v1.service_dependencies import get_user_service
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_admin_or_self,
)
import app.models as models

router = APIRouter()


@router.get("/", response_model=PageResponse[UserResponse], dependencies=[Depends(require_admin)])
async def read_users(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: UserService = Depends(get_user_service),
):
    total = await service.count_users()
    items = await service.get_users(skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=UserResponse)
async def create_user(
    item_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    data = item_in.model_dump()
    data["is_active"] = True
    data["is_verified"] = False
    return await service.create_user(obj_in=data)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: models.User = Depends(get_current_active_user),
):
    return current_user


@router.get("/{id}", response_model=UserResponse)
async def read_user(
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = await service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return db_obj


@router.put("/{id}", response_model=UserResponse)
async def update_user(
    id: UUID,
    item_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = await service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return await service.update_user(db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=UserResponse)
async def delete_user(
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, id)
    db_obj = await service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return await service.delete_user(id=id)


@router.post("/{id}/verify", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def verify_user(
    id: UUID,
    service: UserService = Depends(get_user_service),
):
    """Manually verify a user's email (Admin only)."""
    db_obj = await service.get_user(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return await service.update_user(db_obj=db_obj, obj_in={"is_verified": True})
