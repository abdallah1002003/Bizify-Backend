import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, or_, update
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus
from app.models.notification_setting import NotificationSetting
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification, Any, Any]):
    """Data-access helpers for notifications and notification settings."""

    def get_active_for_user(
        self,
        db: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Notification]:
        """Fetch active notifications for a user, newest first."""
        now = datetime.utcnow()
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    or_(
                        self.model.expires_at.is_(None),
                        self.model.expires_at > now,
                    ),
                    and_(
                        self.model.status != NotificationStatus.ARCHIVED,
                        self.model.status != NotificationStatus.DISMISSED,
                    ),
                )
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, db: Session, notification_id: uuid.UUID) -> Optional[Notification]:
        """Fetch a single notification by its ID."""
        return db.query(self.model).filter(self.model.id == notification_id).first()

    def count_for_user(self, db: Session, user_id: uuid.UUID) -> int:
        """Return the total number of notifications for a user."""
        return db.query(self.model).filter_by(user_id=user_id).count()

    def bulk_update_status(
        self,
        db: Session,
        user_id: uuid.UUID,
        notification_ids: List[uuid.UUID],
        status: NotificationStatus,
    ) -> int:
        """Update multiple notifications to a given status."""
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id,
                )
            )
            .values(status=status)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    def delete_one(self, db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        """Delete a single notification belonging to the user."""
        stmt = delete(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = db.execute(stmt)
        db.commit()
        return bool(result.rowcount)

    def delete_bulk(
        self,
        db: Session,
        user_id: uuid.UUID,
        notification_ids: List[uuid.UUID],
    ) -> int:
        """Delete multiple notifications belonging to the user."""
        if not notification_ids:
            return 0

        stmt = delete(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    def delete_all_for_user(self, db: Session, user_id: uuid.UUID) -> int:
        """Delete all notifications belonging to the user."""
        stmt = delete(Notification).where(Notification.user_id == user_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    def get_or_create_settings(
        self,
        db: Session,
        user_id: uuid.UUID,
    ) -> NotificationSetting:
        """Fetch notification settings or create defaults for a user."""
        settings = (
            db.query(NotificationSetting)
            .filter(NotificationSetting.user_id == user_id)
            .first()
        )
        if not settings:
            settings = NotificationSetting(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    def update_settings(
        self,
        db: Session,
        user_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> NotificationSetting:
        """Update notification settings for a user."""
        settings = self.get_or_create_settings(db, user_id)
        if update_data:
            for key, value in update_data.items():
                setattr(settings, key, value)
            db.commit()
            db.refresh(settings)
        return settings

    def run_maintenance(self, db: Session, *, now: datetime) -> None:
        """Archive expired notifications and delete stale records."""
        db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.expires_at.is_not(None),
                    Notification.expires_at < now,
                    Notification.status != NotificationStatus.ARCHIVED,
                )
            )
            .values(status=NotificationStatus.ARCHIVED)
        )

        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        db.execute(
            delete(Notification)
            .where(
                or_(
                    Notification.created_at < thirty_days_ago,
                    and_(
                        Notification.status == NotificationStatus.ARCHIVED,
                        Notification.created_at < seven_days_ago,
                    ),
                )
            )
        )
        db.commit()


notification_repo = NotificationRepository(Notification)
