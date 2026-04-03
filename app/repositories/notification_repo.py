import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional

from sqlalchemy import and_, delete, or_, update
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus
from app.models.notification_setting import NotificationSetting
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification, Any, Any]):
    """
    Repository for Notification and NotificationSetting database operations.
    """

    def get_active_for_user(
        self, db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[Notification]:
        """
        Fetch active (non-expired, non-archived, non-dismissed) notifications
        for a user, ordered by most recent first.
        """
        now = datetime.utcnow()
        return (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    or_(
                        Notification.expires_at == None,
                        Notification.expires_at > now,
                    ),
                    and_(
                        Notification.status != NotificationStatus.ARCHIVED,
                        Notification.status != NotificationStatus.DISMISSED,
                    ),
                )
            )
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, db: Session, notification_id: uuid.UUID) -> Optional[Notification]:
        """Fetch a single notification by its ID."""
        return db.query(Notification).filter(Notification.id == notification_id).first()

    def count_for_user(self, db: Session, user_id: uuid.UUID) -> int:
        """Return the total number of notifications for a user."""
        return db.query(Notification).filter_by(user_id = user_id).count()

    def bulk_update_status(
        self,
        db: Session,
        user_id: uuid.UUID,
        notification_ids: List[uuid.UUID],
        status: NotificationStatus,
    ) -> int:
        """
        Update multiple notifications to a given status.
        Scoped to the user to prevent IDOR attacks.
        """
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
        """Permanently delete a single notification. Scoped to owner (IDOR protection)."""
        stmt = delete(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    def delete_bulk(
        self, db: Session, user_id: uuid.UUID, notification_ids: List[uuid.UUID]
    ) -> int:
        """Permanently delete multiple notifications. Scoped to owner."""
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
        """Permanently delete every notification for a user."""
        stmt = delete(Notification).where(Notification.user_id == user_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    # --- NotificationSetting helpers ---

    def get_or_create_settings(
        self, db: Session, user_id: uuid.UUID
    ) -> NotificationSetting:
        """
        Fetch user notification preferences, or create a default record if none exists.
        Implements lazy initialization to support legacy users without settings rows.
        """
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
        update_data: dict[str, Any],
    ) -> NotificationSetting:
        settings = self.get_or_create_settings(db, user_id)
        if update_data:
            for key, value in update_data.items():
                setattr(settings, key, value)
            db.commit()
            db.refresh(settings)
        return settings

    def run_maintenance(self, db: Session, *, now: datetime) -> None:
        db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.expires_at != None,
                    Notification.expires_at < now,
                    Notification.status != NotificationStatus.ARCHIVED,
                )
            )
            .values(status = NotificationStatus.ARCHIVED)
        )

        thirty_days_ago = now - timedelta(days = 30)
        seven_days_ago = now - timedelta(days = 7)
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
