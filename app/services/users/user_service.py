import logging
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import Depends

from app.db.database import get_async_db

from app.core.security import get_password_hash
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.models import AdminActionLog, User, UserProfile
from app.models.enums import UserRole
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Service for managing user accounts, profiles, and admin logs (Asynchronous)."""
    db: AsyncSession

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def _record_admin_action(
        self,
        admin_id: Optional[UUID],
        action_type: str,
        target_id: Optional[UUID],
        target_entity: str = "user",
        auto_commit: bool = True
    ) -> AdminActionLog:
        """Records an administrative action in the audit log."""
        if target_id is None:
            raise ValueError("target_id is required for admin log")

        log = AdminActionLog(
            admin_id=admin_id,
            action_type=action_type,
            target_entity=target_entity,
            target_id=target_id,
        )
        self.db.add(log)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(log)
        else:
            await self.db.flush()
        return log

    # ----------------------------
    # User CRUD
    # ----------------------------

    async def get_user(self, id: UUID) -> Optional[User]:
        """Retrieves a user by their unique UUID."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by their registered email address."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves a list of users with pagination."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_users(self) -> int:
        """Returns total count of users."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(User)
        result = await self.db.execute(stmt)
        return cast(int, result.scalar())

    async def create_user(self, obj_in: Union[Dict[str, Any], Any]) -> User:
        """Creates a new user and an associated empty profile."""
        try:
            user_data = _to_update_dict(obj_in)

            if "password" in user_data:
                user_data["password_hash"] = get_password_hash(user_data.pop("password"))
            elif "password_hash" in user_data:
                user_data["password_hash"] = get_password_hash(user_data["password_hash"])

            user_data.setdefault("role", UserRole.ENTREPRENEUR)

            db_obj = User(**user_data)
            self.db.add(db_obj)
            await self.db.flush()

            # Ensure profile exists for new users.
            stmt = select(UserProfile).where(UserProfile.user_id == db_obj.id)
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                profile = UserProfile(user_id=db_obj.id, bio="", preferences_json={})
                self.db.add(profile)

            await self._record_admin_action(
                admin_id=cast(UUID, db_obj.id),
                action_type="USER_CREATED",
                target_id=cast(UUID, db_obj.id),
                target_entity="user",
                auto_commit=False,
            )
            await self.db.commit()
            await self.db.refresh(db_obj)
            logger.info(f"Successfully created user: {db_obj.email} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during create_user: {e}")
            raise

    async def update_user(self, db_obj: User, obj_in: Any) -> User:
        """Updates an existing user's information."""
        update_data = _to_update_dict(obj_in)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        elif "password_hash" in update_data:
            update_data["password_hash"] = get_password_hash(update_data["password_hash"])

        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_user(self, id: UUID) -> Optional[User]:
        """Deletes a user and records the administrative action."""
        db_obj = await self.get_user(id=id)
        if not db_obj:
            return None

        await self._record_admin_action(admin_id=None, action_type="USER_DELETED", target_id=id, auto_commit=False)
        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    # ----------------------------
    # UserProfile CRUD
    # ----------------------------

    async def get_user_profile(
        self,
        id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[UserProfile]:
        """Retrieves a user profile by profile ID or user ID."""
        if id is not None:
            stmt = select(UserProfile).where(UserProfile.id == id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        if user_id is not None:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        return None

    async def get_user_profiles(self, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        """Retrieves multiple user profiles with pagination."""
        stmt = select(UserProfile).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_user_profile(self, obj_in: Any) -> UserProfile:
        """Creates a new user profile manually."""
        db_obj = UserProfile(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_user_profile(
        self,
        db_obj: UserProfile,
        obj_in: Any,
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates an existing user profile record."""
        update_data = _to_update_dict(obj_in)
        _apply_updates(db_obj, update_data)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=cast(UUID, db_obj.user_id),
                target_entity="user_profile",
            )

        return db_obj

    async def update_user_profile_by_user_id(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates a user profile by resolving it via user_id."""
        db_obj = await self.get_user_profile(user_id=user_id)
        if db_obj is None:
            db_obj = UserProfile(user_id=user_id, bio="", preferences_json={})
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)

        _apply_updates(db_obj, profile_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        await self._record_admin_action(
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=cast(UUID, user_id),
            target_entity="user_profile",
        )
        return db_obj

    async def delete_user_profile(self, id: UUID) -> Optional[UserProfile]:
        """Deletes a user profile record."""
        db_obj = await self.get_user_profile(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    # ----------------------------
    # AdminActionLog CRUD
    # ----------------------------

    async def get_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Retrieves a specific admin action log entry."""
        stmt = select(AdminActionLog).where(AdminActionLog.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_admin_action_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        """Retrieves admin action logs with pagination, newest first."""
        stmt = (
            select(AdminActionLog)
            .order_by(AdminActionLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_admin_action_log(self, obj_in: Any) -> AdminActionLog:
        """Creates a new admin action log entry."""
        data = _to_update_dict(obj_in)
        db_obj = AdminActionLog(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_admin_action_log(self, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
        """Updates an existing admin action log entry."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Deletes an admin action log entry."""
        db_obj = await self.get_admin_action_log(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj


async def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db)
