from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
import app.models as models
from app.api.v1.service_dependencies import get_notification_service
from app.core.dependencies import get_current_active_user
from app.schemas.core.notification import NotificationCreate, NotificationUpdate, NotificationResponse
from app.services.core.notification_service import NotificationService

router = APIRouter()


def _ensure_notification_owner(notification: models.Notification, current_user: models.User) -> None:
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[NotificationResponse])
async def read_notifications(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: NotificationService = Depends(get_notification_service),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_notifications(skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    item_in: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return await service.create_notification(obj_in=data)

@router.get("/{id}", response_model=NotificationResponse)
async def read_notification(
    id: UUID,
    service: NotificationService = Depends(get_notification_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_notification(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    _ensure_notification_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=NotificationResponse)
async def update_notification(
    id: UUID,
    item_in: NotificationUpdate,
    service: NotificationService = Depends(get_notification_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_notification(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    _ensure_notification_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return await service.update_notification(db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=NotificationResponse)
async def delete_notification(
    id: UUID,
    service: NotificationService = Depends(get_notification_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_notification(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    _ensure_notification_owner(db_obj, current_user)
    return await service.delete_notification(id=id)
