# ruff: noqa: E402
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File, Notification
from app.services.core.file_service import FileService
from app.services.core.notification_service import NotificationService
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now

logger = logging.getLogger(__name__)


class CoreService(BaseService):
    """Refactored class-based access to core services."""
    async def get_file(self, id: UUID) -> Optional[File]:
        return await get_file(self.db, id)

    async def get_files(self, skip: int = 0, limit: int = 100, owner_id: Optional[UUID] = None) -> List[File]:
        return await get_files(self.db, skip, limit, owner_id)

    async def create_file(self, obj_in: Any) -> File:
        return await create_file(self.db, obj_in)

    async def update_file(self, db_obj: File, obj_in: Any) -> File:
        return await update_file(self.db, db_obj, obj_in)

    async def delete_file(self, id: UUID) -> Optional[File]:
        return await delete_file(self.db, id)

    async def get_notification(self, id: UUID) -> Optional[Notification]:
        return await get_notification(self.db, id)

    async def get_notifications(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[Notification]:
        return await get_notifications(self.db, skip, limit, user_id)

    async def create_notification(self, obj_in: Any) -> Notification:
        return await create_notification(self.db, obj_in)

    async def update_notification(self, db_obj: Notification, obj_in: Any) -> Notification:
        return await update_notification(self.db, db_obj, obj_in)

    async def delete_notification(self, id: UUID) -> Optional[Notification]:
        return await delete_notification(self.db, id)

    async def get_detailed_status(self) -> Dict[str, Any]:
        return await get_detailed_status()

    async def reset_internal_state(self) -> None:
        return await reset_internal_state()


def get_core_service(db: AsyncSession) -> CoreService:
    """Helper to return an instance of CoreService."""
    return CoreService(db)


# ----------------------------
# File (Delegated to FileService)
# ----------------------------

async def get_file(db: AsyncSession, id: UUID) -> Optional[File]:
    return await FileService(db).get_file(id)

async def get_files(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[File]:
    return await FileService(db).get_files(skip, limit, owner_id)

async def create_file(db: AsyncSession, obj_in: Any) -> File:
    return await FileService(db).create_file(obj_in)

async def update_file(db: AsyncSession, db_obj: File, obj_in: Any) -> File:
    return await FileService(db).update_file(db_obj, obj_in)

async def delete_file(db: AsyncSession, id: UUID) -> Optional[File]:
    return await FileService(db).delete_file(id)


# ----------------------------
# Notification (Delegated to NotificationService)
# ----------------------------

async def get_notification(db: AsyncSession, id: UUID) -> Optional[Notification]:
    return cast(Optional[Notification], await NotificationService(db).get_notification(id))

async def get_notifications(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Notification]:
    return await NotificationService(db).get_notifications(skip, limit, user_id)

async def create_notification(db: AsyncSession, obj_in: Any) -> Notification:
    return await NotificationService(db).create_notification(obj_in)

async def update_notification(db: AsyncSession, db_obj: Notification, obj_in: Any) -> Notification:
    return await NotificationService(db).update_notification(db_obj, obj_in)

async def delete_notification(db: AsyncSession, id: UUID) -> Optional[Notification]:
    return await NotificationService(db).delete_notification(id)


# Backward compatibility aliases.
create_file_record = create_file
emit_notification = create_notification


async def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "core_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


async def reset_internal_state() -> None:
    logger.info("core_service reset_internal_state called")
