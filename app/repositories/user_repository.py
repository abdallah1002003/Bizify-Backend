<<<<<<< HEAD
"""
Repository for User domain models:
  - User
  - UserProfile
  - AdminActionLog

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# User services should delegate all persistence to this repository.
"""
=======
>>>>>>> origin/main
from typing import List, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
<<<<<<< HEAD
from sqlalchemy.exc import IntegrityError

from app.models.users.user import User, UserProfile, AdminActionLog
from app.models.enums import UserRole
=======

from app.models.users.user import User
>>>>>>> origin/main
from app.repositories.base_repository import GenericRepository


class UserRepository(GenericRepository[User]):
    """Repository for User model (Asynchronous)."""

<<<<<<< HEAD
    def __init__(self, db: AsyncSession, model: type[User] = User) -> None:
=======
    def __init__(self, db: AsyncSession, model: type[User]) -> None:
>>>>>>> origin/main
        super().__init__(db, model)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        stmt = select(User).options(joinedload(User.profile)).where(User.email == email)
        result = await self.db.execute(stmt)
        return cast(Optional[User], result.scalar_one_or_none())

<<<<<<< HEAD
    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[User]:
        """Create a user safely, returning None on IntegrityError (duplicate email)."""
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[User]:
        """Retrieve a user by Stripe customer ID."""
        stmt = (
            select(User)
            .options(joinedload(User.profile))
            .where(User.stripe_customer_id == stripe_customer_id)
        )
        result = await self.db.execute(stmt)
        return cast(Optional[User], result.scalar_one_or_none())

=======
>>>>>>> origin/main

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
<<<<<<< HEAD

    async def has_admin_user(self) -> bool:
        """Return True if at least one admin account exists."""
        stmt = select(User.id).where(User.role == UserRole.ADMIN).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None


class UserProfileRepository(GenericRepository[UserProfile]):
    """Repository for UserProfile model (Asynchronous)."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, UserProfile)

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """Retrieve a user profile given a user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return cast(Optional[UserProfile], result.scalars().first())

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[UserProfile]:
        """Create a profile safely, returning None on IntegrityError (duplicate user_id)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


class AdminActionLogRepository(GenericRepository[AdminActionLog]):
    """Repository for AdminActionLog model (Asynchronous)."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AdminActionLog)
=======
>>>>>>> origin/main
