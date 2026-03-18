import asyncio
import json
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationRead,
    NotificationList,
    NotificationUpdateStatus,
    NotificationBulkUpdateStatus,
    NotificationSettingRead,
    NotificationSettingUpdate
)
from app.services.notification_service import NotificationService, manager


router = APIRouter()


@router.get("/", response_model = NotificationList)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge = 0),
    limit: int = Query(20, ge = 1, le = 100)
) -> Dict[str, Any]:
    """
    Retrieve a paginated list of active notifications for the current user.
    """
    notifications = NotificationService.get_notifications(db, current_user.id, skip, limit)
    total = db.query(Notification).filter_by(user_id = current_user.id).count()
    
    return {
        "total": total,
        "items": notifications
    }


@router.get("/stream")
async def stream_notifications(
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint for real-time notification push.
    """
    async def event_generator() -> Any:
        queue = await manager.connect(current_user.id)
        try:
            while True:
                # Wait for a new notification
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            manager.disconnect(current_user.id, queue)
            raise

    return StreamingResponse(event_generator(), media_type = "text/event-stream")


@router.patch("/{notification_id}/status", response_model = NotificationRead)
def update_notification_status(
    notification_id: UUID,
    update_data: NotificationUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Notification:
    """
    Update the status of a specific notification (READ or DISMISSED) with IDOR protection.
    """
    return NotificationService.update_status(db, current_user.id, notification_id, update_data.status)


@router.patch("/status/bulk", status_code = status.HTTP_200_OK)
def bulk_update_notifications(
    update_data: NotificationBulkUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Update the status of multiple notifications simultaneously.
    """
    count = NotificationService.bulk_update_status(
        db,
        current_user.id,
        update_data.notification_ids,
        update_data.status
    )
    return {"message": f"Successfully updated {count} notifications"}


@router.get("/settings", response_model = NotificationSettingRead)
async def get_my_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the current user's notification preferences.
    """
    return await NotificationService.get_or_create_settings(db, current_user.id)


@router.patch("/settings", response_model = NotificationSettingRead)
async def update_my_settings(
    update_data: NotificationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update the user's notification preferences.
    """
    settings = await NotificationService.get_or_create_settings(db, current_user.id)
    
    update_dict = update_data.model_dump(exclude_unset = True)
    for key, value in update_dict.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/maintenance", status_code = status.HTTP_204_NO_CONTENT)
def trigger_maintenance(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> None:
    """
    Manually trigger notification maintenance (Archive/Retention).
    Only available to administrators.
    """
    NotificationService.run_maintenance(db)
    return None
