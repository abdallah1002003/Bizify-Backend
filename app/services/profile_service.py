import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.idea import Idea
from app.models.skill_gap_report import SkillGapReport
from app.models.user_profile import UserProfile, GuideStatus
from app.schemas.questionnaire import (
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse,
    UserProfileOutput,
    CareerProfileOutput
)
from app.schemas.user_profile import UserProfileUpdate


logger = logging.getLogger(__name__)


class ProfileService:
    """
    Unified service for managing user profiles, onboarding, and updates.
    """

    @staticmethod
    def get_or_create_profile(db: Session, user_id: uuid.UUID) -> UserProfile:
        """
        Retrieves an existing profile or creates a new one for the given user ID.
        """
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            profile = UserProfile(user_id = user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
        return profile

    @staticmethod
    def submit_full_questionnaire(
        db: Session,
        user_id: uuid.UUID,
        answers: List[QuestionnaireAnswer]
    ) -> QuestionnaireResponse:
        """
        Parses the dynamic list of questionnaire answers, maps them to the profile keys,
        saves the data, and returns the structured response.
        """
        profile = ProfileService.get_or_create_profile(db, user_id)
        
        user_profile_data = {}
        career_profile_data = {}
        
        mapping = {
            "Q_q1": ("user_profile", "curiosity_domain"),
            "Q_q2": ("user_profile", "experience_level"),
            "Q_q3": ("user_profile", "business_interests"),
            "Q_q4": ("user_profile", "target_region"),
            "Q_q5": ("user_profile", "founder_setup"),
            "Q_q6_risk": ("user_profile", "risk_tolerance"),
            
            "career_q1_free_day": ("career_profile", "free_day_preferences"),
            "career_q2_work_type": ("career_profile", "preferred_work_types"),
            "career_q3_problem_type": ("career_profile", "problem_solving_styles"),
            "career_q4_environment": ("career_profile", "preferred_work_environments"),
            "career_q5_impact": ("career_profile", "desired_impact"),
        }
        
        for answer in answers:
            if answer.field in mapping:
                category, target_key = mapping[answer.field]
                value = answer.choices if answer.multi else (answer.choices[0] if answer.choices else None)
                
                # Cleanup some values based on user's examples (e.g. 'Beginner (Just starting...)' -> 'Beginner')
                if isinstance(value, str):
                    if "(" in value:
                        value = value.split(" (")[0].strip()
                    if "moderate risk" in value.lower():
                        value = "moderate"
                
                if category == "user_profile":
                    user_profile_data[target_key] = value
                else:
                    career_profile_data[target_key] = value

        # Save to database JSON columns
        profile.interests_json = user_profile_data.get("business_interests", [])
        profile.background_json = user_profile_data
        profile.personality_json = career_profile_data
        
        profile.onboarding_completed = True
        profile.guide_status = GuideStatus.COMPLETED
        
        # Generate personalization summary
        interests_text = ", ".join(profile.interests_json) if profile.interests_json else "various fields"
        exp_level = user_profile_data.get("experience_level", "N/A")
        profile.personalization_profile = f"User interested in {interests_text} with {exp_level} experience level."
        
        db.commit()
        
        return QuestionnaireResponse(
            user_profile=UserProfileOutput(**user_profile_data),
            career_profile=CareerProfileOutput(**career_profile_data)
        )

    @staticmethod
    def skip_questionnaire(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """
        Skips the onboarding questionnaire and marks it as completed with default settings.
        """
        profile = ProfileService.get_or_create_profile(db, user_id)
        
        profile.onboarding_completed = True
        profile.guide_status = GuideStatus.SKIPPED
        # Wait, I should check the actual Enum name used in the file.
        # Looking at profile_service.py, it doesn't import GuideStatus yet.
        
        db.commit()
        return {"status": "success", "message": "Onboarding skipped"}

    @staticmethod
    def restart_questionnaire(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """
        Resets all questionnaire data and allows the user to start over.
        """
        profile = ProfileService.get_or_create_profile(db, user_id)
        
        profile.interests_json = None
        profile.background_json = None
        profile.personality_json = None
        profile.personalization_profile = None
        profile.onboarding_completed = False
        profile.guide_status = "not_started"
        
        db.commit()
        return {"status": "success", "message": "Questionnaire reset successfully"}

    @staticmethod
    def update_guide_status(
        db: Session,
        user_id: uuid.UUID,
        status_in: GuideStatusUpdate
    ) -> Dict[str, Any]:
        """
        Updates the guide status for the user profile.
        """
        profile = ProfileService.get_or_create_profile(db, user_id)
        
        profile.guide_status = status_in.status
        
        db.commit()
        
        return {
            "message": "Guide status updated successfully",
            "status": profile.guide_status
        }

    @staticmethod
    def update_profile(
        db: Session, 
        user_id: uuid.UUID, 
        profile_in: UserProfileUpdate
    ) -> Optional[UserProfile]:
        """
        Updates the user profile with change detection, transactions, and logging (UC_14).
        """
        profile = ProfileService.get_or_create_profile(db, user_id)

        update_data = profile_in.model_dump(exclude_unset = True)
        is_changed = False
        
        for field, value in update_data.items():
            current_value = getattr(profile, field)
            if current_value != value:
                is_changed = True
                break
        
        if not is_changed:
            return profile

        try:
            for field, value in update_data.items():
                setattr(profile, field, value)
            
            ProfileService.invalidate_dependencies(db, user_id, profile)
            
            db.commit()
            db.refresh(profile)
            
            return profile
        except Exception as e:
            logger.error(f"CRITICAL: Profile update failed for user {user_id}. Error: {str(e)}")
            db.rollback()
            raise e

    @staticmethod
    def invalidate_dependencies(db: Session, user_id: uuid.UUID, profile: UserProfile) -> None:
        """
        Marks dependent records as outdated to trigger re-analysis.
        """
        db.query(SkillGapReport).filter(SkillGapReport.user_id == user_id).update(
            {"is_outdated": True}
        )
        
        db.query(Idea).filter(Idea.owner_id == user_id).update(
            {"is_score_outdated": True}
        )
        
        profile.personalization_profile = None
