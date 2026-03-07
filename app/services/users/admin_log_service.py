# ruff: noqa
"""
Admin Action Log CRUD operations (Async).
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AdminActionLog
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.services.base_service import BaseService
from app.repositories.user_repository import AdminActionLogRepository

logger = logging.getLogger(__name__)


class AdminLogService(BaseService):
    """Service for managing AdminActionLog records."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = AdminActionLogRepository(db)

    async def get_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Get admin action log by ID."""
        return await self.repo.get(id)

    async def get_admin_action_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        """Get admin action logs with pagination."""
        logs = await self.repo.get_all()
        logs.sort(key=lambda x: x.created_at, reverse=True)
        return logs[skip:skip+limit]

    async def create_admin_action_log(self, obj_in: Any, auto_commit: bool = True) -> AdminActionLog:
        """Create a new admin action log."""
        return await self.repo.create(_to_update_dict(obj_in), auto_commit=auto_commit)

    async def update_admin_action_log(self, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
        """Update an admin action log."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Delete an admin action log."""
        db_obj = await self.get_admin_action_log(id)
        if db_obj:
            return await self.repo.delete(db_obj)
        return None

    async def get_admin_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        """Backward-compatible alias for get_admin_action_logs."""
        return await self.get_admin_action_logs(skip=skip, limit=limit)
async def get_admin_log_service(db: AsyncSession) -> AdminLogService:
    """Dependency provider for AdminLogService."""
    return AdminLogService(db)
