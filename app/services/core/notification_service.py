"""
Notification CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.core_repository import NotificationRepository

logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """Service for managing Notification records."""
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = NotificationRepository(db)

    async def get_notification(self, id: UUID) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        return cast(Optional[Notification], await self.repo.get(id))

    async def get_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Notification]:
        """Retrieve multiple notifications with optional user filtering."""
        if user_id is not None:
            results = await self.repo.get_for_user(user_id, skip=skip, limit=limit)
            return results
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_notification(self, obj_in: Any) -> Notification:
        """Create a new notification record."""
        return cast(Notification, await self.repo.create(_to_update_dict(obj_in)))

    async def update_notification(self, db_obj: Notification, obj_in: Any) -> Notification:
        """Update an existing notification record."""
        return cast(Notification, await self.repo.update(db_obj, _to_update_dict(obj_in)))

    async def delete_notification(self, id: UUID) -> Optional[Notification]:
        """Delete a notification record."""
        return cast(Optional[Notification], await self.repo.delete(id))

async def get_notification_service(db: AsyncSession) -> NotificationService:
    """Dependency provider for NotificationService."""
    return NotificationService(db)
