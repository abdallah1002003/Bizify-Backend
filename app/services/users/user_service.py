
import logging
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


from app.core.security import get_password_hash
from app.core.crud_utils import _to_update_dict
from app.models import AdminActionLog, User, UserProfile
from app.models.enums import UserRole
from app.services.base_service import BaseService
from app.repositories.user_repository import UserRepository, UserProfileRepository

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Service for managing user accounts, profiles, and admin logs (Asynchronous)."""
    db: AsyncSession

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.user_repo = UserRepository(db, User)
        self.profile_repo = UserProfileRepository(db)
        from app.services.users.admin_log_service import AdminLogService
        self.admin_log_service = AdminLogService(db)

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

        log_data = {
            "admin_id": admin_id,
            "action_type": action_type,
            "target_entity": target_entity,
            "target_id": target_id,
        }
        
        return await self.admin_log_service.create_admin_action_log(log_data, auto_commit=auto_commit)

    # ----------------------------
    # User CRUD
    # ----------------------------

    async def get_user(self, id: UUID) -> Optional[User]:
        """Retrieves a user by their unique UUID."""
        return await self.user_repo.get_with_profile(id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by their registered email address."""
        return await self.user_repo.get_by_email(email)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves a list of users with pagination."""
        return await self.user_repo.get_all_with_profiles(skip, limit)

    async def count_users(self) -> int:
        """Returns total count of users."""
        return await self.user_repo.count()

    async def has_admin_user(self) -> bool:
        """Returns whether at least one admin user exists."""
        return await self.user_repo.has_admin_user()


    async def create_user(self, obj_in: Union[Dict[str, Any], Any]) -> User:
        """Creates a new user and an associated empty profile."""
        try:
            user_data = _to_update_dict(obj_in)

            if "password" in user_data:
                user_data["password_hash"] = get_password_hash(user_data.pop("password"))
            elif "password_hash" in user_data:
                user_data["password_hash"] = get_password_hash(user_data["password_hash"])

            user_data.setdefault("role", UserRole.ENTREPRENEUR)

            db_obj = await self.user_repo.create(user_data, auto_commit=False)

            # Ensure profile exists for new users.
            profile = await self.profile_repo.get_by_user_id(db_obj.id)
            if not profile:
                await self.profile_repo.create({
                    "user_id": db_obj.id,
                    "bio": "", 
                    "preferences_json": {}
                }, auto_commit=False)

            await self._record_admin_action(
                admin_id=cast(UUID, db_obj.id),
                action_type="USER_CREATED",
                target_id=cast(UUID, db_obj.id),
                target_entity="user",
                auto_commit=False,
            )
            await self.user_repo.commit()
            await self.user_repo.refresh(db_obj)
            logger.info(f"Successfully created user: {db_obj.email} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            await self.user_repo.rollback()
            logger.error(f"Transaction failed during create_user: {e}")
            raise

    async def update_user(self, db_obj: User, obj_in: Any) -> User:
        """Updates an existing user's information."""
        update_data = _to_update_dict(obj_in)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        elif "password_hash" in update_data:
            update_data["password_hash"] = get_password_hash(update_data["password_hash"])

        return await self.user_repo.update(db_obj, update_data)

    async def delete_user(self, id: UUID) -> Optional[User]:
        """Deletes a user and records the administrative action."""
        db_obj = await self.get_user(id=id)
        if not db_obj:
            return None

        await self._record_admin_action(admin_id=None, action_type="USER_DELETED", target_id=id, auto_commit=False)
        await self.user_repo.delete(db_obj.id)
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
            return await self.profile_repo.get(id)

        if user_id is not None:
            return await self.profile_repo.get_by_user_id(user_id)
        return None

    async def get_user_profiles(self, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        """Retrieves multiple user profiles with pagination."""
        return await self.profile_repo.get_all(skip=skip, limit=limit)

    async def create_user_profile(self, obj_in: Any) -> UserProfile:
        """Creates a new user profile manually."""
        return await self.profile_repo.create(_to_update_dict(obj_in))

    async def update_user_profile(
        self,
        db_obj: UserProfile,
        obj_in: Any,
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates an existing user profile record."""
        updated = await self.profile_repo.update(db_obj, _to_update_dict(obj_in))

        if performer_id is not None:
            await self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=cast(UUID, updated.user_id),
                target_entity="user_profile",
            )

        return updated

    async def update_user_profile_by_user_id(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates a user profile by resolving it via user_id."""
        db_obj = await self.get_user_profile(user_id=user_id)
        if db_obj is None:
            db_obj = await self.profile_repo.create({"user_id": user_id, "bio": "", "preferences_json": {}})

        updated = await self.profile_repo.update(db_obj, profile_data)

        await self._record_admin_action(
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=cast(UUID, user_id),
            target_entity="user_profile",
        )
        return updated

    async def delete_user_profile(self, id: UUID) -> Optional[UserProfile]:
        """Deletes a user profile record."""
        db_obj = await self.get_user_profile(id=id)
        if db_obj:
            return await self.profile_repo.delete(db_obj)
        return None

    # ----------------------------
    # AdminActionLog CRUD (Delegated to AdminLogService)
    # ----------------------------

    async def get_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        return await self.admin_log_service.get_admin_action_log(id)

    async def get_admin_action_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        return await self.admin_log_service.get_admin_action_logs(skip, limit)

    async def create_admin_action_log(self, obj_in: Any) -> AdminActionLog:
        return await self.admin_log_service.create_admin_action_log(obj_in)

    async def update_admin_action_log(self, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
        return await self.admin_log_service.update_admin_action_log(db_obj, obj_in)

    async def delete_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        return await self.admin_log_service.delete_admin_action_log(id)


async def get_user_service(db: AsyncSession) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db)
