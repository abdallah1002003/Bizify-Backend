import logging
import uuid
from typing import Any, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_skill import UserSkill


logger = logging.getLogger(__name__)


class SkillGapService:
    """
    Service for managing individual user skills.
    """

    @staticmethod
    def get_user_skills(db: Session, user_id: uuid.UUID) -> List[UserSkill]:
        """Retrieves all skills for the specified user."""
        return db.query(UserSkill).filter(UserSkill.user_id == user_id).all()

    @staticmethod
    def add_user_skill(db: Session, user_id: uuid.UUID, skill_in: Any) -> UserSkill:
        """Adds a new single skill for the user."""
        existing = db.query(UserSkill).filter(
            UserSkill.user_id == user_id, 
            UserSkill.skill_name == skill_in.skill_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Skill already exists for this user."
            )
            
        new_skill = UserSkill(
            user_id=user_id, 
            skill_name=skill_in.skill_name, 
            declared_level=skill_in.declared_level
        )
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)
        return new_skill

    @staticmethod
    def update_user_skill(db: Session, user_id: uuid.UUID, skill_id: uuid.UUID, skill_in: Any) -> UserSkill:
        """Updates an existing skill for the user."""
        skill = db.query(UserSkill).filter(UserSkill.id == skill_id, UserSkill.user_id == user_id).first()
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
            
        skill.skill_name = skill_in.skill_name
        skill.declared_level = skill_in.declared_level
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete_user_skill(db: Session, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        """Deletes a specific user skill."""
        skill = db.query(UserSkill).filter(UserSkill.id == skill_id, UserSkill.user_id == user_id).first()
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
            
        db.delete(skill)
        db.commit()