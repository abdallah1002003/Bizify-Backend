from typing import List, Optional, cast
from sqlalchemy import select, func
from uuid import UUID
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.user import User, AdminActionLog, UserProfile
from app.repositories.base_repository import GenericRepository


class UserRepository(GenericRepository[User]):
    """Repository for User model (Asynchronous)."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        stmt = select(User).options(joinedload(User.profile)).where(User.email == email)
        result = await self.db.execute(stmt)
        return cast(Optional[User], result.scalar_one_or_none())

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[User]:
        """Create a user safely, returning None on IntegrityError (duplicate email)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


    async def get_with_profile(self, id: UUID) -> Optional[User]:
        """Retrieve a user by ID, eager loading their profile."""
        stmt = select(User).options(joinedload(User.profile)).where(User.id == id)
        result = await self.db.execute(stmt)
        return cast(Optional[User], result.scalar_one_or_none())


    async def get_all_with_profiles(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieve all users, eager loading their profiles."""
        stmt = select(User).options(joinedload(User.profile)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return cast(List[User], list(result.scalars().all()))

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[User]:
        """Retrieve a user by their Stripe customer ID."""
        stmt = select(User).where(User.stripe_customer_id == stripe_customer_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_admin_user(self) -> bool:
        """Check if any admin user exists in the system."""
        from app.models.enums import UserRole
        stmt = select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0


class UserProfileRepository(GenericRepository[UserProfile]):
    """Repository for UserProfile model."""
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserProfile)

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """Retrieve a profile by user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class AdminActionLogRepository(GenericRepository[AdminActionLog]):
    """Repository for AdminActionLog model."""
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminActionLog)
