import uuid
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate


class UserRepository(BaseRepository[User, UserCreate, UserCreate]):
    """Data-access helpers for `User` records."""

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Fetch a user by email address."""
        return db.query(self.model).filter(self.model.email == email).first()

    def get_by_google_id(self, db: Session, google_id: str) -> Optional[User]:
        """Fetch a user by Google account identifier."""
        return db.query(self.model).filter(self.model.google_id == google_id).first()

    def get_active_user(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Fetch an active, verified user by identifier."""
        return (
            db.query(self.model)
            .filter(
                self.model.id == user_id,
                self.model.is_active.is_(True),
                self.model.is_verified.is_(True),
            )
            .first()
        )

    def get_by_role(self, db: Session, role: Union[str, UserRole]) -> List[User]:
        """Fetch all users with a specific role."""
        return db.query(self.model).filter(self.model.role == role).all()

    def get_first_by_role(self, db: Session, role: Union[str, UserRole]) -> Optional[User]:
        """Fetch the first user matching a specific role."""
        return db.query(self.model).filter(self.model.role == role).first()

    def count_all(self, db: Session) -> int:
        """Return the total number of users."""
        return db.query(self.model).count()

    def count_inactive(self, db: Session) -> int:
        """Return the total number of inactive users."""
        return db.query(self.model).filter(self.model.is_active.is_(False)).count()


user_repo = UserRepository(User)
