import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.models.notification import DeliveryStatus, Notification, NotificationStatus
from app.models.notification_setting import NotificationSetting
from app.repositories.notification_repo import notification_repo
from app.repositories.user_repo import user_repo

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class ConnectionManager:
    """Track active SSE connections for notifications."""

    def __init__(self) -> None:
        self.active_connections: Dict[UUID, List[asyncio.Queue]] = {}

    async def connect(self, user_id: UUID) -> asyncio.Queue:
        """Create and register a queue for a user connection."""
        queue = asyncio.Queue()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(queue)
        return queue

    def disconnect(self, user_id: UUID, queue: asyncio.Queue) -> None:
        """Remove a queue from the user's active connections."""
        if user_id not in self.active_connections:
            return

        self.active_connections[user_id].remove(queue)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def push_notification(self, user_id: UUID, data: Dict[str, Any]) -> None:
        """Push a notification payload to all active queues for a user."""
        if user_id not in self.active_connections:
            return

        for queue in self.active_connections[user_id]:
            await queue.put(data)


manager = ConnectionManager()


class NotificationService:
    """Notification delivery, status, and settings workflows."""

    @staticmethod
    async def get_or_create_settings(db: Session, user_id: UUID) -> NotificationSetting:
        """Fetch or initialize notification settings."""
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
        should_force_email: bool = False,
    ) -> Optional[Notification]:
        """Create a notification and schedule any needed secondary delivery."""
        settings = await NotificationService.get_or_create_settings(db, user_id)
        notification = notification_repo.create(
            db,
            obj_in={
                "user_id": user_id,
                "title": title,
                "content": content,
                "message": content,
                "type": notify_type,
                "expires_at": expires_at,
                "delivery_status": DeliveryStatus.PENDING,
            },
        )

        if not should_force_email and settings.is_enabled and settings.push_enabled:
            payload = {
                "id": str(notification.id),
                "title": notification.title,
                "content": notification.content,
                "type": notification.type,
                "created_at": notification.created_at.isoformat(),
            }
            await manager.push_notification(user_id, payload)

        if should_force_email or settings.is_enabled:
            if should_force_email:
                background_tasks.add_task(
                    NotificationService.trigger_secondary_delivery,
                    db,
                    notification.id,
                )
                return notification

            is_marketing = notify_type.lower() == "marketing"
            is_team = notify_type.lower() in [
                "team_join",
                "team_invite",
                "team_update",
                "team_response",
                "team_removal",
            ]
            is_billing = notify_type.lower() == "billing"

            should_send = True
            if is_marketing and not settings.marketing_enabled:
                should_send = False
            elif is_team and not settings.team_updates_enabled:
                should_send = False
            elif is_billing and not settings.billing_alerts_enabled:
                should_send = False

            if should_send:
                background_tasks.add_task(
                    NotificationService.trigger_secondary_delivery,
                    db,
                    notification.id,
                )

        return notification

    @staticmethod
    async def trigger_secondary_delivery(db: Session, notification_id: UUID) -> None:
        """Handle secondary delivery and retry state changes."""
        notification = notification_repo.get_by_id(db, notification_id)
        if not notification:
            return

        user = user_repo.get(db, notification.user_id)
        settings = notification_repo.get_or_create_settings(db, notification.user_id)
        if not user or not (settings.email_enabled or settings.sms_enabled):
            return

        try:
            logger.info(
                "Delivering notification %s to user %s",
                notification.id,
                user.email,
            )
            notification.delivery_status = DeliveryStatus.SENT
            notification_repo.save(db, db_obj=notification)
        except Exception:
            logger.exception("Failed to deliver notification %s", notification.id)
            notification.retry_count += 1
            notification.delivery_status = (
                DeliveryStatus.PENDING
                if notification.retry_count < MAX_RETRIES
                else DeliveryStatus.FAILED
            )
            notification_repo.save(db, db_obj=notification)

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Notification]:
        """Fetch active notifications with pagination."""
        return notification_repo.get_active_for_user(db, user_id, skip=skip, limit=limit)

    @staticmethod
    def count_notifications(db: Session, user_id: UUID) -> int:
        """Return the total number of notifications for a user."""
        return notification_repo.count_for_user(db, user_id)

    @staticmethod
    def update_status(
        db: Session,
        user_id: UUID,
        notification_id: UUID,
        status: NotificationStatus,
    ) -> Notification:
        """Update the status of a notification after ownership validation."""
        notification = notification_repo.get_by_id(db, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return notification_repo.update(db, db_obj=notification, obj_in={"status": status})

    @staticmethod
    def bulk_update_status(
        db: Session,
        user_id: UUID,
        notification_ids: List[UUID],
        status: NotificationStatus,
    ) -> int:
        """Update multiple notifications for a user."""
        return notification_repo.bulk_update_status(db, user_id, notification_ids, status)

    @staticmethod
    def update_settings(
        db: Session,
        user_id: UUID,
        update_data: Dict[str, Optional[bool]],
    ) -> NotificationSetting:
        """Update notification settings for a user."""
        return notification_repo.update_settings(db, user_id, update_data)

    @staticmethod
    def run_maintenance(db: Session) -> None:
        """Archive expired notifications and remove stale records."""
        notification_repo.run_maintenance(db, now=datetime.utcnow())

    @staticmethod
    def delete_notification(db: Session, user_id: UUID, notification_id: UUID) -> bool:
        """Delete a single notification for a user."""
        return notification_repo.delete_one(db, user_id, notification_id)

    @staticmethod
    def bulk_delete_notifications(
        db: Session,
        user_id: UUID,
        notification_ids: List[UUID],
    ) -> int:
        """Delete multiple notifications for a user."""
        return notification_repo.delete_bulk(db, user_id, notification_ids)

    @staticmethod
    def delete_all_notifications(db: Session, user_id: UUID) -> int:
        """Delete all notifications for a user."""
        return notification_repo.delete_all_for_user(db, user_id)
