from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
<<<<<<< HEAD
import app.models as models
from app.api.v1.service_dependencies import get_usage_service
from app.core.dependencies import get_current_active_user
from app.schemas.billing.usage import UsageCreate, UsageUpdate, UsageResponse
from app.services.billing.usage_service import UsageService
=======
from sqlalchemy.ext.asyncio import AsyncSession
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_async_db
from app.schemas.billing.usage import UsageCreate, UsageUpdate, UsageResponse
from app.services.billing import usage_service as service
>>>>>>> origin/main

router = APIRouter()


def _ensure_usage_owner(usage: models.Usage, current_user: models.User) -> None:
    if usage.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[UsageResponse])
async def read_usages(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
<<<<<<< HEAD
    service: UsageService = Depends(get_usage_service),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_usages(skip=skip, limit=limit, user_id=current_user.id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_usages(db, skip=skip, limit=limit, user_id=current_user.id)
>>>>>>> origin/main

@router.post("/", response_model=UsageResponse)
async def create_usage(
    item_in: UsageCreate,
<<<<<<< HEAD
    service: UsageService = Depends(get_usage_service),
=======
    db: AsyncSession = Depends(get_async_db),
>>>>>>> origin/main
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
<<<<<<< HEAD
    return await service.create_usage(obj_in=data)
=======
    return await service.create_usage(db, obj_in=data)
>>>>>>> origin/main

@router.get("/{id}", response_model=UsageResponse)
async def read_usage(
    id: UUID,
<<<<<<< HEAD
    service: UsageService = Depends(get_usage_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=UsageResponse)
async def update_usage(
    id: UUID,
    item_in: UsageUpdate,
<<<<<<< HEAD
    service: UsageService = Depends(get_usage_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
<<<<<<< HEAD
    return await service.update_usage(db_obj=db_obj, obj_in=data)
=======
    return await service.update_usage(db, db_obj=db_obj, obj_in=data)
>>>>>>> origin/main

@router.delete("/{id}", response_model=UsageResponse)
async def delete_usage(
    id: UUID,
<<<<<<< HEAD
    service: UsageService = Depends(get_usage_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    return await service.delete_usage(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_usage(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Usage not found")
    _ensure_usage_owner(db_obj, current_user)
    return await service.delete_usage(db, id=id)
>>>>>>> origin/main
