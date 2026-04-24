import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.predefined_skill import PredefinedSkill
from app.models.skill_category import SkillCategory
from app.models.user_skill import UserSkill
from app.repositories.base import BaseRepository


# ── UserSkill repository ──────────────────────────────────────────────────────

class SkillRepository(BaseRepository[UserSkill, Any, Any]):
    """Repository for UserSkill-specific database operations."""

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
        """Check if a user already has a skill with the given name (case-insensitive)."""
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.skill_name.ilike(skill_name),
            )
            .first()
        )

    def get_by_user_and_id(
        self, db: Session, user_id: uuid.UUID, skill_id: uuid.UUID
    ) -> Optional[UserSkill]:
        """Fetch a skill by its ID, scoped to a specific user (IDOR protection)."""
        return (
            db.query(self.model)
            .filter(
                self.model.id == skill_id,
                self.model.user_id == user_id,
            )
            .first()
        )


skill_repo = SkillRepository(UserSkill)


# ── SkillCategory repository ──────────────────────────────────────────────────

class SkillCategoryRepository(BaseRepository[SkillCategory, Any, Any]):
    """Repository for skill categories with their predefined skills."""

    def get_all_with_skills(self, db: Session) -> List[SkillCategory]:
        """Return all categories, each eagerly loaded with its predefined skills."""
        return (
            db.query(self.model)
            .options(joinedload(self.model.predefined_skills))
            .order_by(self.model.name)
            .all()
        )

    def get_by_name(self, db: Session, name: str) -> Optional[SkillCategory]:
        return db.query(self.model).filter(self.model.name == name).first()


skill_category_repo = SkillCategoryRepository(SkillCategory)


# ── PredefinedSkill repository ────────────────────────────────────────────────

class PredefinedSkillRepository(BaseRepository[PredefinedSkill, Any, Any]):
    """Repository for predefined skills."""

    def get_by_category(
        self, db: Session, category_id: uuid.UUID
    ) -> List[PredefinedSkill]:
        return (
            db.query(self.model)
            .filter(self.model.category_id == category_id)
            .order_by(self.model.name)
            .all()
        )

    def search_by_name(
        self, db: Session, query: str
    ) -> List[PredefinedSkill]:
        """Case-insensitive search across all predefined skills, returns all matches."""
        return (
            db.query(self.model)
            .filter(self.model.name.ilike(f"%{query}%"))
            .options(joinedload(self.model.category))
            .order_by(self.model.name)
            .all()
        )


predefined_skill_repo = PredefinedSkillRepository(PredefinedSkill)
