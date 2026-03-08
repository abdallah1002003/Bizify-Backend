from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models import Notification
from app.services.base_service import BaseService
from app.repositories.core_repository import NotificationRepository

logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """Service for managing Notification records."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = NotificationRepository(db)

    async def get_notification(self, id: UUID) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        return await self.repo.get(id)

    async def get_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Notification]:
        """Retrieve multiple notifications with optional user filtering."""
        if user_id is not None:
            return await self.repo.get_for_user(user_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_notification(self, obj_in: Any) -> Notification:
        """Create a new notification record."""
        return await self.repo.create(obj_in)

    async def update_notification(self, db_obj: Notification, obj_in: Any) -> Notification:
        """Update an existing notification record."""
        return await self.repo.update(db_obj, obj_in)

    async def delete_notification(self, id: UUID) -> Optional[Notification]:
        """Delete a notification record."""
        return await self.repo.delete(id)

async def get_notification_service(db: AsyncSession = Depends(get_async_db)) -> NotificationService:
    """Dependency provider for NotificationService."""
    return NotificationService(db)

# ----------------------------
# Legacy Async Aliases
# ----------------------------

async def get_notification(db: AsyncSession, id: UUID) -> Optional[Notification]:
    """Legacy async alias for getting a notification."""
    return await NotificationService(db).get_notification(id)

async def get_notifications(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Notification]:
    """Legacy async alias for getting multiple notifications."""
    return await NotificationService(db).get_notifications(skip, limit, user_id)

async def create_notification(db: AsyncSession, obj_in: Any) -> Notification:
    """Legacy async alias for creating a notification."""
    return await NotificationService(db).create_notification(obj_in)

async def update_notification(db: AsyncSession, db_obj: Notification, obj_in: Any) -> Notification:
    """Legacy async alias for updating a notification."""
    return await NotificationService(db).update_notification(db_obj, obj_in)

async def delete_notification(db: AsyncSession, id: UUID) -> Optional[Notification]:
    """Legacy async alias for deleting a notification."""
    return await NotificationService(db).delete_notification(id)

# Backward compatibility alias
emit_notification = create_notification
