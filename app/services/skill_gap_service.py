import uuid
from typing import Any, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_skill import UserSkill
from app.repositories.skill_repo import skill_repo


class SkillGapService:
    """
    Service for managing individual user skills.
    All DB operations are delegated to skill_repo.
    Business logic: duplicate detection, ownership validation (IDOR), 404 errors.
    """

    @staticmethod
    def get_user_skills(db: Session, user_id: uuid.UUID) -> List[UserSkill]:
        """Return all skills registered by the user."""
        return skill_repo.get_by_user(db, user_id)

    @staticmethod
    def add_user_skill(db: Session, user_id: uuid.UUID, skill_in: Any) -> UserSkill:
        """
        Add a new skill for the user.
        Business rule: rejects duplicate skill names for the same user.
        """
        existing = skill_repo.get_by_user_and_name(db, user_id, skill_in.skill_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill already exists for this user.",
            )
        return skill_repo.create(db, obj_in={
            "user_id": user_id,
            "skill_name": skill_in.skill_name,
            "declared_level": skill_in.declared_level,
        })

    @staticmethod
    def update_user_skill(
        db: Session, user_id: uuid.UUID, skill_id: uuid.UUID, skill_in: Any
    ) -> UserSkill:
        """
        Update an existing skill.
        Business rule: validates the skill belongs to this user before updating (IDOR protection).
        """
        skill = skill_repo.get_by_user_and_id(db, user_id, skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found.",
            )
        return skill_repo.update(db, db_obj=skill, obj_in={
            "skill_name": skill_in.skill_name,
            "declared_level": skill_in.declared_level,
        })

    @staticmethod
    def delete_user_skill(db: Session, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        """
        Delete a skill.
        Business rule: validates ownership before deleting (IDOR protection).
        """
        skill = skill_repo.get_by_user_and_id(db, user_id, skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found.",
            )
        skill_repo.remove(db, id=skill_id)