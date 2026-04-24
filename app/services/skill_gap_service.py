import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.skill_category import SkillCategory
from app.models.user_skill import UserSkill
from app.repositories.skill_repo import (
    predefined_skill_repo,
    skill_category_repo,
    skill_repo,
)
from app.schemas.skill_gap import UserSkillCreate


class SkillGapService:
    """
    Service for managing entrepreneur skills.

    Rules:
    - An entrepreneur can select any number of predefined skills.
    - An entrepreneur can also type a custom skill name (is_custom=True).
    - Duplicate skill names (case-insensitive) for the same user are rejected.
    """

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_all_categories(db: Session) -> List[SkillCategory]:
        """Return all skill categories with their predefined skills."""
        return skill_category_repo.get_all_with_skills(db)

    @staticmethod
    def get_user_skills(db: Session, user_id: uuid.UUID) -> List[UserSkill]:
        """Return all skills selected by the user."""
        return skill_repo.get_by_user(db, user_id)

    @staticmethod
    def search_predefined_skills(db: Session, query: str) -> list:
        """Search predefined skills by name and return results with their category name."""
        if not query or not query.strip():
            return []
        results = predefined_skill_repo.search_by_name(db, query.strip())
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "category_id": skill.category_id,
                "category_name": skill.category.name if skill.category else "",
            }
            for skill in results
        ]

    # ── Write ─────────────────────────────────────────────────────────────────

    @staticmethod
    def add_user_skill(
        db: Session, user_id: uuid.UUID, skill_in: UserSkillCreate
    ) -> UserSkill:
        """
        Add a skill to the user's profile.

        - If predefined_skill_id is provided → look it up and use its name.
        - If not → skill_name must be provided (custom skill).
        """
        # ── resolve skill name ────────────────────────────────────────────────
        if skill_in.predefined_skill_id:
            predefined = predefined_skill_repo.get(db, skill_in.predefined_skill_id)
            if not predefined:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Predefined skill not found.",
                )
            skill_name = predefined.name
            category_id = predefined.category_id
            is_custom = False
        else:
            if not skill_in.skill_name or not skill_in.skill_name.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Provide either predefined_skill_id or a skill_name for a custom skill.",
                )
            skill_name = skill_in.skill_name.strip()
            category_id = None
            is_custom = True

        # ── duplicate check ───────────────────────────────────────────────────
        if skill_repo.get_by_user_and_name(db, user_id, skill_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill '{skill_name}' is already in your profile.",
            )

        return skill_repo.create(db, obj_in={
            "user_id": user_id,
            "skill_name": skill_name,
            "is_custom": is_custom,
            "predefined_skill_id": skill_in.predefined_skill_id,
            "category_id": category_id,
        })

    @staticmethod
    def delete_user_skill(
        db: Session, user_id: uuid.UUID, skill_id: uuid.UUID
    ) -> None:
        """Delete a skill (ownership validated)."""
        skill = skill_repo.get_by_user_and_id(db, user_id, skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found.",
            )
        skill_repo.remove(db, id=skill_id)