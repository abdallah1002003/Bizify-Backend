from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
import app.models as models
from app.api.v1.service_dependencies import get_payment_method_service
from app.core.dependencies import get_current_active_user
from app.schemas.billing.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.services.billing.payment_method import PaymentMethodService

router = APIRouter()


def _ensure_payment_method_owner(payment_method: models.PaymentMethod, current_user: models.User) -> None:
    if payment_method.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[PaymentMethodResponse])
async def read_payment_methods(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_payment_methods(skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=PaymentMethodResponse)
async def create_payment_method(
    item_in: PaymentMethodCreate,
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return await service.create_payment_method(obj_in=data)

@router.get("/{id}", response_model=PaymentMethodResponse)
async def read_payment_method(
    id: UUID,
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    id: UUID,
    item_in: PaymentMethodUpdate,
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return await service.update_payment_method(db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=PaymentMethodResponse)
async def delete_payment_method(
    id: UUID,
    service: PaymentMethodService = Depends(get_payment_method_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_payment_method(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return await service.delete_payment_method(id=id)
