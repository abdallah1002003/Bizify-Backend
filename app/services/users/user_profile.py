"""
User Profile CRUD operations (Async).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import UserProfile, AdminActionLog
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


async def _record_admin_action(
    db: AsyncSession,
    admin_id: Optional[UUID],
    action_type: str,
    target_id: Optional[UUID],
    target_entity: str = "user_profile",
) -> None:
    """Async admin action logging."""
    if target_id is None:
        raise ValueError("target_id is required for admin log")

    log = AdminActionLog(
        admin_id=admin_id,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
    )
    db.add(log)
    await db.commit()


# ----------------------------
# UserProfile CRUD (Async)
# ----------------------------

async def get_user_profile(
    db: AsyncSession,
    id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
) -> Optional[UserProfile]:
    """Get user profile by ID or user_id."""
    if id is not None:
        return await db.get(UserProfile, id)

    if user_id is not None:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    return None


async def get_user_profiles(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[UserProfile]:
    """Get user profiles with pagination."""
    stmt = select(UserProfile).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_user_profile(db: AsyncSession, obj_in: Any) -> UserProfile:
    """Create a new user profile."""
    db_obj = UserProfile(**_to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user_profile(
    db: AsyncSession,
    db_obj: UserProfile,
    obj_in: Any,
    performer_id: Optional[UUID] = None,
) -> UserProfile:
    """Update a user profile explicitly by passing the UserProfile db object."""
    update_data = _to_update_dict(obj_in)
    _apply_updates(db_obj, update_data)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    if performer_id is not None:
        await _record_admin_action(
            db,
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=db_obj.user_id,
            target_entity="user_profile",
        )

    return db_obj


async def update_user_profile_by_user_id(
    db: AsyncSession,
    user_id: UUID,
    profile_data: Dict[str, Any],
    performer_id: Optional[UUID] = None,
) -> UserProfile:
    """Update a user profile by resolving the user_id first."""
    db_obj = await get_user_profile(db, user_id=user_id)
    if db_obj is None:
        db_obj = UserProfile(user_id=user_id, bio="", preferences_json={})
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

    _apply_updates(db_obj, profile_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    if performer_id is not None:
        await _record_admin_action(
            db,
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=user_id,
            target_entity="user_profile",
        )
    
    return db_obj


async def delete_user_profile(db: AsyncSession, id: UUID) -> Optional[UserProfile]:
    """Delete a user profile."""
    db_obj = await get_user_profile(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj
