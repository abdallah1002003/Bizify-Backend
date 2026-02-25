from typing import Optional
from uuid import UUID

from sqlalchemy.orm import joinedload

from app.models.users.user import User
from app.repositories.base_repository import GenericRepository


class UserRepository(GenericRepository[User]):
    """Repository for User model."""

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        return self.db.query(User).options(joinedload(User.profile)).filter(User.email == email).first()  # type: ignore[no-any-return]

    def get_with_profile(self, id: UUID) -> Optional[User]:
        """Retrieve a user by ID, eager loading their profile."""
        return self.db.query(User).options(joinedload(User.profile)).filter(User.id == id).first()  # type: ignore[no-any-return]

    def get_all_with_profiles(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Retrieve all users, eager loading their profiles."""
        return self.db.query(User).options(joinedload(User.profile)).offset(skip).limit(limit).all()  # type: ignore[no-any-return]
