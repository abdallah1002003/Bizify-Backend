from typing import List, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.user import User
from app.repositories.base_repository import GenericRepository


class UserRepository(GenericRepository[User]):
    """Repository for User model (Asynchronous)."""

    def __init__(self, db: AsyncSession, model: type[User]) -> None:
        super().__init__(db, model)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        stmt = select(User).options(joinedload(User.profile)).where(User.email == email)
        result = await self.db.execute(stmt)
        return cast(Optional[User], result.scalar_one_or_none())


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
