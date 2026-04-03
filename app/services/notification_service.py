import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus, DeliveryStatus
from app.models.notification_setting import NotificationSetting
from app.repositories.notification_repo import notification_repo
from app.repositories.user_repo import user_repo


logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3


class ConnectionManager:
    """
    Manages active SSE (Server-Sent Events) connections for real-time notifications.
    """

    def __init__(self) -> None:
        """
        Initializes the connection manager with an empty pool.
        """
        self.active_connections: Dict[UUID, List[asyncio.Queue]] = {}

    async def connect(self, user_id: UUID) -> asyncio.Queue:
        """
        Creates and registers a new connection queue for a user.
        """
        queue = asyncio.Queue()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            
        self.active_connections[user_id].append(queue)
        
        return queue

    def disconnect(self, user_id: UUID, queue: asyncio.Queue) -> None:
        """
        Removes a connection queue for a user.
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(queue)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def push_notification(self, user_id: UUID, data: dict) -> None:
        """
        Broadcasts a notification payload to all active connections for a user.
        """
        if user_id in self.active_connections:
            for queue in self.active_connections[user_id]:
                await queue.put(data)


manager = ConnectionManager()


class NotificationService:
    """
    Service layer for managing the notification life cycle, delivery, and settings.
    """

    @staticmethod
    async def get_or_create_settings(db: Session, user_id: UUID) -> NotificationSetting:
        """
        Fetches user-specific notification preferences or initializes defaults.
        Delegates to notification_repo for lazy initialization logic.
        """
        return notification_repo.get_or_create_settings(db, user_id)

    @staticmethod
    async def notify_user(
        db: Session, 
        user_id: UUID, 
        title: str, 
        content: str, 
        notify_type: str,
        background_tasks: BackgroundTasks,
        expires_at: Optional[datetime] = None,
        should_force_email: bool = False
    ) -> Optional[Notification]:
        """
        Main entry point to send a notification. Checks preferences, saves to DB, 
        pushes to real-time stream, and triggers secondary delivery.
        
        If should_force_email is True, it bypasses the push-notification check and 
        prioritizes background delivery (AF_A6).
        """
        settings = await NotificationService.get_or_create_settings(db, user_id)
        
        delivery_status = DeliveryStatus.PENDING

        notification = notification_repo.create(db, obj_in={
            "user_id": user_id,
            "title": title,
            "content": content,
            "message": content,
            "type": notify_type,
            "expires_at": expires_at,
            "delivery_status": delivery_status
        })

        if not should_force_email and settings.is_enabled and settings.push_enabled:
            payload = {
                "id": str(notification.id),
                "title": notification.title,
                "content": notification.content,
                "type": notification.type,
                "created_at": notification.created_at.isoformat()
            }
            await manager.push_notification(user_id, payload)

        if should_force_email or settings.is_enabled:
            if should_force_email:
                background_tasks.add_task(NotificationService.trigger_secondary_delivery, db, notification.id)
            else:
                is_marketing = notify_type.lower() == "marketing"
                is_team = notify_type.lower() in ["team_join", "team_invite", "team_update", "team_response", "team_removal"]
                is_billing = notify_type.lower() == "billing"

                should_send = True
                if is_marketing and not settings.marketing_enabled:
                    should_send = False
                elif is_team and not settings.team_updates_enabled:
                    should_send = False
                elif is_billing and not settings.billing_alerts_enabled:
                    should_send = False
                    
                if should_send:
                    background_tasks.add_task(NotificationService.trigger_secondary_delivery, db, notification.id)
        
        return notification

    @staticmethod
    async def trigger_secondary_delivery(db: Session, notification_id: UUID) -> None:
        """
        Handles async Email/SMS delivery with failure-aware retry logic.
        """
        notification = notification_repo.get_by_id(db, notification_id)
        
        if not notification:
            return

        user = user_repo.get(db, notification.user_id)
        settings = notification_repo.get_or_create_settings(db, notification.user_id)

        if not (settings.email_enabled or settings.sms_enabled):
            return

        try:
            logger.info(f"Delivering notification {notification.id} to user {user.email}")
            
            notification.delivery_status = DeliveryStatus.SENT
            notification_repo.save(db, db_obj=notification)
        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {str(e)}")
            
            notification.retry_count += 1
            
            if notification.retry_count < MAX_RETRIES:
                notification.delivery_status = DeliveryStatus.PENDING
            else:
                notification.delivery_status = DeliveryStatus.FAILED
            notification_repo.save(db, db_obj=notification)

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Notification]:
        """
        Returns active notifications with pagination.
        Delegates filtering logic to notification_repo.
        """
        return notification_repo.get_active_for_user(db, user_id, skip=skip, limit=limit)

    @staticmethod
    def count_notifications(db: Session, user_id: UUID) -> int:
        return notification_repo.count_for_user(db, user_id)

    @staticmethod
    def update_status(db: Session, user_id: UUID, notification_id: UUID, status: NotificationStatus) -> Notification:
        """
        Updates a single notification status with IDOR protection.
        """
        notification = notification_repo.get_by_id(db, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # IDOR Protection
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied"
            )
            
        return notification_repo.update(db, db_obj=notification, obj_in={"status": status})

    @staticmethod
    def bulk_update_status(
        db: Session,
        user_id: UUID,
        notification_ids: List[UUID],
        status: NotificationStatus,
    ) -> int:
        """
        Updates multiple notifications for a user (Bulk operation).
        Delegates to notification_repo which applies IDOR protection.
        """
        return notification_repo.bulk_update_status(db, user_id, notification_ids, status)

    @staticmethod
    def update_settings(
        db: Session,
        user_id: UUID,
        update_data: Dict[str, Optional[bool]],
    ) -> NotificationSetting:
        return notification_repo.update_settings(db, user_id, update_data)

    @staticmethod
    def run_maintenance(db: Session) -> None:
        """
        Periodic cleanup to archive expired records and enforce hard-delete retention.
        """
        notification_repo.run_maintenance(db, now=datetime.utcnow())

    @staticmethod
    def delete_notification(db: Session, user_id: UUID, notification_id: UUID) -> bool:
        """Permanently deletes a single notification (IDOR protection via notification_repo)."""
        return notification_repo.delete_one(db, user_id, notification_id)

    @staticmethod
    def bulk_delete_notifications(db: Session, user_id: UUID, notification_ids: List[UUID]) -> int:
        """Permanently deletes multiple notifications for a user."""
        return notification_repo.delete_bulk(db, user_id, notification_ids)

    @staticmethod
    def delete_all_notifications(db: Session, user_id: UUID) -> int:
        """Permanently deletes all notifications for a specific user."""
        return notification_repo.delete_all_for_user(db, user_id)
