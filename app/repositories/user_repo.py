from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserCreate]):
    """
    Repository for User-specific database operations.
    Inherits base CRUD operations (get, get_multi, create, update, remove)
    from BaseRepository and adds User-specific queries below.
    """

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        Used in login, password recovery, and registration duplicate checks.
        """
        return db.query(self.model).filter(self.model.email == email).first()

    def get_active_user(self, db: Session, user_id: str) -> Optional[User]:
        """
        Fetch a user only if they are active and not locked.
        Centralizes the 'active user' logic so it never gets duplicated across services.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.id == user_id,
                self.model.is_active == True,
                self.model.is_verified == True,
            )
            .first()
        )

    def get_by_role(self, db: Session, role: str) -> list[User]:
        """
        Fetch all users with a specific role (e.g. 'ADMIN', 'USER').
        """
        return db.query(self.model).filter(self.model.role == role).all()


# A ready-to-use singleton instance.
# Import this object directly in any Service or dependency:
# from app.repositories.user_repo import user_repo
user_repo = UserRepository(User)
