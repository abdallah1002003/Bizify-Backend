from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
<<<<<<< HEAD
import app.models as models
from app.api.v1.service_dependencies import get_payment_method_service
from app.core.dependencies import get_current_active_user
from app.schemas.billing.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.services.billing.payment_method import PaymentMethodService
=======
from sqlalchemy.ext.asyncio import AsyncSession
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_async_db
from app.schemas.billing.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.services.billing import payment_method as service
>>>>>>> origin/main

router = APIRouter()


def _ensure_payment_method_owner(payment_method: models.PaymentMethod, current_user: models.User) -> None:
    if payment_method.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[PaymentMethodResponse])
async def read_payment_methods(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
<<<<<<< HEAD
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_payment_methods(skip=skip, limit=limit, user_id=current_user.id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_payment_methods(db, skip=skip, limit=limit, user_id=current_user.id)
>>>>>>> origin/main

@router.post("/", response_model=PaymentMethodResponse)
async def create_payment_method(
    item_in: PaymentMethodCreate,
<<<<<<< HEAD
    service: PaymentMethodService = Depends(get_payment_method_service),
=======
    db: AsyncSession = Depends(get_async_db),
>>>>>>> origin/main
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
<<<<<<< HEAD
    return await service.create_payment_method(obj_in=data)
=======
    return await service.create_payment_method(db, obj_in=data)
>>>>>>> origin/main

@router.get("/{id}", response_model=PaymentMethodResponse)
async def read_payment_method(
    id: UUID,
<<<<<<< HEAD
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    id: UUID,
    item_in: PaymentMethodUpdate,
<<<<<<< HEAD
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(db, id=id)
>>>>>>> origin/main
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
<<<<<<< HEAD
    return await service.update_payment_method(db_obj=db_obj, obj_in=data)
=======
    return await service.update_payment_method(db, db_obj=db_obj, obj_in=data)
>>>>>>> origin/main

@router.delete("/{id}", response_model=PaymentMethodResponse)
async def delete_payment_method(
    id: UUID,
<<<<<<< HEAD
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return await service.delete_payment_method(id=id)
=======
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return await service.delete_payment_method(db, id=id)
>>>>>>> origin/main
