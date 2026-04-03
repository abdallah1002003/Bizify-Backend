import asyncio
import json
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.schemas.notification import (
    NotificationRead,
    NotificationList,
    NotificationUpdateStatus,
    NotificationBulkUpdateStatus,
    NotificationBulkDelete,
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
    total = NotificationService.count_notifications(db, current_user.id)
    
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
            yield f"data: {json.dumps({'message': 'Stream connected'})}\n\n"
            
            while True:
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
 ) -> Any:
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
    update_dict = update_data.model_dump(exclude_unset = True)
    return NotificationService.update_settings(db, current_user.id, update_dict)


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


@router.post("/test-notify", status_code = status.HTTP_201_CREATED)
async def send_test_notification(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Sends a test notification to the current user to verify the real-time stream and list.
    """
    await NotificationService.notify_user(
        db,
        current_user.id,
        title = "Test Notification",
        content = "This is a real-time test notification from Bizify!",
        notify_type = "general",
        background_tasks = background_tasks
    )
    return {"message": "Test notification sent successfully"}


@router.delete("/{notification_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Permanently delete a specific notification (IDOR protection).
    """
    success = NotificationService.delete_notification(db, current_user.id, notification_id)
    if not success:
        raise HTTPException(status_code = 404, detail = "Notification not found")
    return None


@router.post("/bulk-delete", status_code = status.HTTP_200_OK)
def bulk_delete_notifications(
    delete_data: NotificationBulkDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Permanently delete multiple notifications for the current user.
    """
    count = NotificationService.bulk_delete_notifications(
        db,
        current_user.id,
        delete_data.notification_ids
    )
    return {"message": f"Successfully deleted {count} notifications"}


@router.delete("/status/all", status_code = status.HTTP_200_OK)
def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Permanently delete all notifications for the current user.
    """
    count = NotificationService.delete_all_notifications(db, current_user.id)
    return {"message": f"Successfully deleted all {count} notifications"}
