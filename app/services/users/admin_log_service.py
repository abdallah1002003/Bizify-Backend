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
from app.services.base_service import BaseService
from app.repositories.user_repository import AdminActionLogRepository
from app.core.crud_utils import _to_update_dict, _apply_updates

class AdminLogService(BaseService):
    """Refactored class-based access to admin logs."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = AdminActionLogRepository(db)
    async def get_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Get admin action log by ID."""
        return await self.repo.get(id)

    async def get_admin_action_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        """Get admin action logs with pagination."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_admin_action_log(self, obj_in: Any) -> AdminActionLog:
        """Create a new admin action log."""
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_admin_action_log(self, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
        """Update an admin action log."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Delete an admin action log."""
        return await self.repo.delete(id)


def get_admin_log_service(db: AsyncSession) -> AdminLogService:
    """Helper to return an instance of AdminLogService."""
    return AdminLogService(db)

# Backward-compatible aliases (Deprecated)
async def get_admin_action_log(db: AsyncSession, id: UUID) -> Optional[AdminActionLog]:
    return await AdminLogService(db).get_admin_action_log(id)

async def get_admin_action_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return await AdminLogService(db).get_admin_action_logs(skip, limit)

async def create_admin_action_log(db: AsyncSession, obj_in: Any) -> AdminActionLog:
    return await AdminLogService(db).create_admin_action_log(obj_in)

async def update_admin_action_log(db: AsyncSession, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
    return await AdminLogService(db).update_admin_action_log(db_obj, obj_in)

async def delete_admin_action_log(db: AsyncSession, id: UUID) -> Optional[AdminActionLog]:
    return await AdminLogService(db).delete_admin_action_log(id)

async def get_admin_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return await AdminLogService(db).get_admin_action_logs(skip, limit)
