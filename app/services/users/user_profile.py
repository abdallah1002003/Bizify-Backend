
"""
User Profile CRUD operations (Async).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserProfile
from app.core.crud_utils import _to_update_dict
from app.services.base_service import BaseService
from app.repositories.user_repository import UserProfileRepository, AdminActionLogRepository

logger = logging.getLogger(__name__)


class UserProfileService(BaseService):
    """Service for managing UserProfile records with optional admin audit logging."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = UserProfileRepository(db)
        from app.services.users.admin_log_service import AdminLogService
        self.admin_log_service = AdminLogService(db)


    async def _record_admin_action(
        self,
        admin_id: Optional[UUID],
        action_type: str,
        target_id: Optional[UUID],
        target_entity: str = "user_profile",
    ) -> None:
        """Log admin action using AdminLogService."""
        if target_id is None:
            raise ValueError("target_id is required for admin log")
        
        await self.admin_log_service.create_admin_action_log({
            "admin_id": admin_id,
            "action_type": action_type,
            "target_entity": target_entity,
            "target_id": target_id,
        }, auto_commit=False)

    async def get_user_profile(
        self,
        id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[UserProfile]:
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
        db_obj = await self.repo.update(db_obj, _to_update_dict(obj_in))

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=db_obj.user_id,
                target_entity="user_profile",
            )
        return db_obj

    async def update_user_profile_by_user_id(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Update a user profile by resolving the user_id first (upsert)."""
        db_obj = await self.get_user_profile(user_id=user_id)
        if db_obj is None:
            db_obj = await self.repo.create({
                "user_id": user_id, 
                "bio": "", 
                "preferences_json": {}
            })

        db_obj = await self.repo.update(db_obj, profile_data)

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=user_id,
                target_entity="user_profile",
            )
        return db_obj

    async def delete_user_profile(self, id: UUID) -> Optional[UserProfile]:
        """Delete a user profile."""
        db_obj = await self.get_user_profile(id=id)
        if db_obj:
            return await self.repo.delete(db_obj)
        return None
async def get_user_profile_service(db: AsyncSession) -> UserProfileService:
    """Dependency provider for UserProfileService."""
    return UserProfileService(db)
