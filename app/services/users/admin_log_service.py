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

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# AdminActionLog CRUD (Async)
# ----------------------------

async def get_admin_action_log(db: AsyncSession, id: UUID) -> Optional[AdminActionLog]:
    """Get admin action log by ID."""
    return await db.get(AdminActionLog, id)


async def get_admin_action_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    """Get admin action logs with pagination."""
    stmt = select(AdminActionLog).order_by(AdminActionLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_admin_action_log(db: AsyncSession, obj_in: Any) -> AdminActionLog:
    """Create a new admin action log."""
    data = _to_update_dict(obj_in)
    db_obj = AdminActionLog(**data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_admin_action_log(db: AsyncSession, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
    """Update an admin action log."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_admin_action_log(db: AsyncSession, id: UUID) -> Optional[AdminActionLog]:
    """Delete an admin action log."""
    db_obj = await get_admin_action_log(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj


# Backward-compatible alias used by older code.
async def get_admin_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return await get_admin_action_logs(db, skip=skip, limit=limit)
