from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.models.enums import UserRole
from app.schemas.users.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.services.users.user_service import UserService
from app.api.v1.service_dependencies import get_user_service
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_admin_or_self,
    is_admin_or_self,
)
import app.models as models

router = APIRouter()


@router.get("/", response_model=List[UserProfileResponse], dependencies=[Depends(require_admin)])
async def read_user_profiles(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: UserService = Depends(get_user_service),
):
    return await service.get_user_profiles(skip=skip, limit=limit)


@router.post("/", response_model=UserProfileResponse)
async def create_user_profile(
    item_in: UserProfileCreate,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    require_admin_or_self(current_user, item_in.user_id)
    if not is_admin_or_self(current_user, item_in.user_id) or current_user.role != UserRole.ADMIN:
        item_in.user_id = current_user.id
    return await service.create_user_profile(obj_in=item_in)


@router.get("/{id}", response_model=UserProfileResponse)
async def read_user_profile(
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_user_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    require_admin_or_self(current_user, db_obj.user_id)
    return db_obj


@router.put("/{id}", response_model=UserProfileResponse)
async def update_user_profile(
    id: UUID,
    item_in: UserProfileUpdate,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_user_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    require_admin_or_self(current_user, db_obj.user_id)
    if current_user.role != UserRole.ADMIN:
        item_in.user_id = db_obj.user_id
    return await service.update_user_profile(db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=UserProfileResponse)
async def delete_user_profile(
    id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_user_profile(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    require_admin_or_self(current_user, db_obj.user_id)
    return await service.delete_user_profile(id=id)
