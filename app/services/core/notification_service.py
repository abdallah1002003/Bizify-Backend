"""
Notification CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional, cast
from uuid import UUID

<<<<<<< HEAD
=======
from fastapi import Depends
from sqlalchemy import select
>>>>>>> origin/main
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.services.base_service import BaseService
<<<<<<< HEAD
from app.core.crud_utils import _to_update_dict
from app.repositories.core_repository import NotificationRepository
=======
from app.db.database import get_async_db
from app.core.crud_utils import _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """Service for managing Notification records."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = NotificationRepository(db)

    async def get_notification(self, id: UUID) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        return cast(Optional[Notification], await self.repo.get(id))
=======
    async def get_notification(self, id: UUID) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        stmt = select(Notification).where(Notification.id == id)
        result = await self.db.execute(stmt)
        return cast(Optional[Notification], result.scalar_one_or_none())
>>>>>>> origin/main

    async def get_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Notification]:
        """Retrieve multiple notifications with optional user filtering."""
<<<<<<< HEAD
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
=======
        stmt = select(Notification).offset(skip).limit(limit)
        if user_id is not None:
            stmt = stmt.where(Notification.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_notification(self, obj_in: Any) -> Notification:
        """Create a new notification record."""
        db_obj = Notification(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_notification(self, db_obj: Notification, obj_in: Any) -> Notification:
        """Update an existing notification record."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_notification(self, id: UUID) -> Optional[Notification]:
        """Delete a notification record."""
        db_obj = await self.get_notification(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return cast(Optional[Notification], db_obj)

async def get_notification_service(db: AsyncSession = Depends(get_async_db)) -> NotificationService:
    """Dependency provider for NotificationService."""
    return NotificationService(db)

# ----------------------------
# Legacy Async Aliases
# ----------------------------

async def get_notification(db: AsyncSession, id: UUID) -> Optional[Notification]:
    """Legacy async alias for getting a notification."""
    return cast(Optional[Notification], await NotificationService(db).get_notification(id))

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
    return cast(Optional[Notification], await NotificationService(db).delete_notification(id))

# Backward compatibility alias
emit_notification = create_notification
>>>>>>> origin/main
