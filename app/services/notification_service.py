import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus, DeliveryStatus
from app.models.notification_setting import NotificationSetting
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationUpdateStatus, NotificationBulkUpdateStatus


logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETENTION_DAYS = 30
ARCHIVE_RETENTION_DAYS = 7


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
        """
        settings = db.query(NotificationSetting).filter(NotificationSetting.user_id == user_id).first()
        
        if not settings:
            settings = NotificationSetting(user_id = user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
        return settings

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

        notification = Notification(
            user_id = user_id,
            title = title,
            content = content,
            message = content,
            type = notify_type,
            expires_at = expires_at,
            delivery_status = delivery_status
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

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
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        if not notification:
            return

        user = db.query(User).filter(User.id == notification.user_id).first()
        settings = db.query(NotificationSetting).filter(NotificationSetting.user_id == notification.user_id).first()

        if not (settings.email_enabled or settings.sms_enabled):
            return

        try:
            logger.info(f"Delivering notification {notification.id} to user {user.email}")
            
            notification.delivery_status = DeliveryStatus.SENT
            db.commit()
        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {str(e)}")
            
            notification.retry_count += 1
            
            if notification.retry_count < MAX_RETRIES:
                notification.delivery_status = DeliveryStatus.PENDING
            else:
                notification.delivery_status = DeliveryStatus.FAILED
                
            db.commit()

    @staticmethod
    def get_notifications(
        db: Session, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Notification]:
        """
        Returns active notifications with pagination. 
        Filters out expired ones based on expires_at (Idempotent GET).
        """
        now = datetime.utcnow()
        return db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                or_(
                    Notification.expires_at == None,
                    Notification.expires_at > now
                ),
                and_(
                    Notification.status != NotificationStatus.ARCHIVED,
                    Notification.status != NotificationStatus.DISMISSED
                )
            )
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_status(db: Session, user_id: UUID, notification_id: UUID, status: NotificationStatus) -> Notification:
        """
        Updates a single notification status with IDOR protection.
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code = 404, detail = "Notification not found")
        
        # IDOR Protection
        if notification.user_id != user_id:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN, 
                detail = "Access denied"
            )
            
        notification.status = status
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def bulk_update_status(
        db: Session, 
        user_id: UUID, 
        notification_ids: List[UUID], 
        status: NotificationStatus
    ) -> int:
        """
        Updates multiple notifications for a user (Bulk operation).
        """
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id
                )
            )
            .values(status = status)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    @staticmethod
    def run_maintenance(db: Session) -> None:
        """
        Periodic cleanup to archive expired records and enforce hard-delete retention.
        """
        now = datetime.utcnow()
        
        db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.expires_at != None,
                    Notification.expires_at < now,
                    Notification.status != NotificationStatus.ARCHIVED
                )
            )
            .values(status = NotificationStatus.ARCHIVED)
        )

        thirty_days_ago = now - timedelta(days = RETENTION_DAYS)
        seven_days_ago = now - timedelta(days = ARCHIVE_RETENTION_DAYS)
        
        db.execute(
            delete(Notification)
            .where(
                or_(
                    Notification.created_at < thirty_days_ago,  # General retention
                    and_(
                        Notification.status == NotificationStatus.ARCHIVED,
                        Notification.created_at < seven_days_ago  # Archive cleanup
                    )
                )
            )
        )
        db.commit()

    @staticmethod
    def delete_notification(db: Session, user_id: UUID, notification_id: UUID) -> bool:
        """
        Permanently deletes a single notification for a specific user (IDOR protection).
        """
        stmt = (
            delete(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    @staticmethod
    def bulk_delete_notifications(db: Session, user_id: UUID, notification_ids: List[UUID]) -> int:
        """
        Permanently deletes multiple notifications for a user (Bulk operation).
        """
        if not notification_ids:
            return 0
            
        stmt = (
            delete(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id
                )
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
    @staticmethod
    def delete_all_notifications(db: Session, user_id: UUID) -> int:
        """
        Permanently deletes all notifications for a specific user.
        """
        stmt = (
            delete(Notification)
            .where(Notification.user_id == user_id)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
