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
from app.services.base_service import BaseService
from app.repositories.user_repository import UserProfileRepository, AdminActionLogRepository
from app.core.crud_utils import _to_update_dict, _apply_updates

class UserProfileService(BaseService):
    """Refactored class-based access to user profiles."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = UserProfileRepository(db)
        self.admin_log_repo = AdminActionLogRepository(db)
    async def get_user_profile(self, id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> Optional[UserProfile]:
        """Get user profile by ID or user_id."""
        if id is not None:
            return await self.repo.get(id)
        if user_id is not None:
            return await self.repo.get_by_user_id(user_id)
        return None

    async def get_user_profiles(self, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        """Get user profiles with pagination."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_user_profile(self, obj_in: Any) -> UserProfile:
        """Create a new user profile."""
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_user_profile(
        self,
        db_obj: UserProfile,
        obj_in: Any,
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Update a user profile explicitly by passing the UserProfile db object."""
        update_data = _to_update_dict(obj_in)
        updated = await self.repo.update(db_obj, update_data)

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=db_obj.user_id,
            )
        return updated

    async def update_user_profile_by_user_id(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Update a user profile by resolving the user_id first."""
        db_obj = await self.get_user_profile(user_id=user_id)
        if db_obj is None:
            db_obj = await self.repo.create({"user_id": user_id, "bio": "", "preferences_json": {}})

        updated = await self.repo.update(db_obj, profile_data)

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=user_id,
            )
        return updated

    async def delete_user_profile(self, id: UUID) -> Optional[UserProfile]:
        """Delete a user profile."""
        return await self.repo.delete(id)

    async def _record_admin_action(
        self,
        admin_id: Optional[UUID],
        action_type: str,
        target_id: Optional[UUID],
        target_entity: str = "user_profile",
        auto_commit: bool = True,
    ) -> AdminActionLog:
        """Record an administrative action."""
        if target_id is None:
            raise ValueError("target_id is required for admin log")

        return await self.admin_log_repo.create({
            "admin_id": admin_id,
            "action_type": action_type,
            "target_entity": target_entity,
            "target_id": target_id,
        }, auto_commit=auto_commit)


def get_user_profile_service(db: AsyncSession) -> UserProfileService:
    """Helper to return an instance of UserProfileService."""
    return UserProfileService(db)

# Backward-compatible aliases (Deprecated)
async def get_user_profile(
    db: AsyncSession,
    id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
) -> Optional[UserProfile]:
    return await UserProfileService(db).get_user_profile(id, user_id)

async def get_user_profiles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserProfile]:
    return await UserProfileService(db).get_user_profiles(skip, limit)

async def create_user_profile(db: AsyncSession, obj_in: Any) -> UserProfile:
    return await UserProfileService(db).create_user_profile(obj_in)

async def update_user_profile(db: AsyncSession, db_obj: UserProfile, obj_in: Any, performer_id: Optional[UUID] = None) -> UserProfile:
    return await UserProfileService(db).update_user_profile(db_obj, obj_in, performer_id)

async def update_user_profile_by_user_id(db: AsyncSession, user_id: UUID, profile_data: Dict[str, Any], performer_id: Optional[UUID] = None) -> UserProfile:
    return await UserProfileService(db).update_user_profile_by_user_id(user_id, profile_data, performer_id)

async def delete_user_profile(db: AsyncSession, id: UUID) -> Optional[UserProfile]:
    return await UserProfileService(db).delete_user_profile(id)

async def _record_admin_action(db: AsyncSession, admin_id: Optional[UUID], action_type: str, target_id: Optional[UUID], target_entity: str = "user_profile", auto_commit: bool = True) -> AdminActionLog:
    return await UserProfileService(db)._record_admin_action(admin_id, action_type, target_id, target_entity, auto_commit)
