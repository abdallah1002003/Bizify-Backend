import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.user_skill import UserSkill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository[UserSkill, Any, Any]):
    """
    Repository for UserSkill-specific database operations.
    """

    def get_by_user(self, db: Session, user_id: uuid.UUID) -> List[UserSkill]:
        """Fetch all skills registered by a specific user."""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .all()
        )

    def get_by_user_and_name(
        self, db: Session, user_id: uuid.UUID, skill_name: str
    ) -> Optional[UserSkill]:
        """
        Check if a user already has a skill with the given name.
        Used to prevent duplicate skill entries.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.skill_name == skill_name,
            )
            .first()
        )

    def get_by_user_and_id(
        self, db: Session, user_id: uuid.UUID, skill_id: uuid.UUID
    ) -> Optional[UserSkill]:
        """
        Fetch a skill by its ID, scoped to a specific user.
        Prevents users from modifying or deleting other users' skills (IDOR protection).
        """
        return (
            db.query(self.model)
            .filter(
                self.model.id == skill_id,
                self.model.user_id == user_id,
            )
            .first()
        )


skill_repo = SkillRepository(UserSkill)
