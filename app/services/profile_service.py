import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user_profile import GuideStatus, UserProfile
from app.repositories.idea_repo import idea_repo
from app.repositories.profile_repo import profile_repo
from app.schemas.questionnaire import (
    CareerProfileOutput,
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse,
    UserProfileOutput,
)
from app.schemas.user_profile import UserProfileUpdate

logger = logging.getLogger(__name__)


class ProfileService:
    """User profile, onboarding, and questionnaire workflows."""

    @staticmethod
    def get_or_create_profile(db: Session, user_id: uuid.UUID) -> UserProfile:
        """Fetch an existing profile or lazily create one."""
        return profile_repo.get_or_create(db, user_id)

    @staticmethod
    def submit_full_questionnaire(
        db: Session,
        user_id: uuid.UUID,
        answers: List[QuestionnaireAnswer],
    ) -> QuestionnaireResponse:
        """Map questionnaire answers into structured profile data."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        user_profile_data: Dict[str, Any] = {}
        career_profile_data: Dict[str, Any] = {}
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
            if answer.field not in mapping:
                continue

            category, target_key = mapping[answer.field]
            value = answer.choices if answer.multi else (answer.choices[0] if answer.choices else None)
            if isinstance(value, str):
                if "(" in value:
                    value = value.split(" (")[0].strip()
                if "moderate risk" in value.lower():
                    value = "moderate"

            if category == "user_profile":
                user_profile_data[target_key] = value
            else:
                career_profile_data[target_key] = value

        profile.interests_json = user_profile_data.get("business_interests", [])
        profile.background_json = user_profile_data
        profile.personality_json = career_profile_data
        profile.onboarding_completed = True
        profile.guide_status = GuideStatus.COMPLETED

        interests_text = ", ".join(profile.interests_json) if profile.interests_json else "various fields"
        experience_level = user_profile_data.get("experience_level", "N/A")
        profile.personalization_profile = (
            f"User interested in {interests_text} with {experience_level} experience level."
        )
        profile_repo.save(db, db_obj=profile)

        return QuestionnaireResponse(
            user_profile=UserProfileOutput(**user_profile_data),
            career_profile=CareerProfileOutput(**career_profile_data),
        )

    @staticmethod
    def finalize_onboarding(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """Mark onboarding as completed."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.onboarding_completed = True
        profile.guide_status = GuideStatus.COMPLETED
        profile_repo.save(db, db_obj=profile)
        return {"status": "success", "message": "Onboarding finalized"}

    @staticmethod
    def skip_questionnaire(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """Skip only the questionnaire portion of onboarding."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.onboarding_completed = True
        profile_repo.save(db, db_obj=profile)
        return {"status": "success", "message": "Onboarding questionnaire skipped"}

    @staticmethod
    def skip_guide(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """Skip only the beginner guide."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.guide_status = GuideStatus.SKIPPED
        profile_repo.save(db, db_obj=profile)
        return {"status": "success", "message": "Beginner guide skipped"}

    @staticmethod
    def restart_questionnaire(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
        """Reset questionnaire-derived profile data."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.interests_json = None
        profile.background_json = None
        profile.personality_json = None
        profile.personalization_profile = None
        profile.onboarding_completed = False
        profile.guide_status = GuideStatus.NOT_STARTED
        profile_repo.save(db, db_obj=profile)
        return {"status": "success", "message": "Questionnaire reset successfully"}

    @staticmethod
    def update_guide_status(
        db: Session,
        user_id: uuid.UUID,
        status_in: GuideStatusUpdate,
    ) -> Dict[str, Any]:
        """Update the guide status for a user."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.guide_status = status_in.status
        profile_repo.save(db, db_obj=profile)
        return {
            "message": "Guide status updated successfully",
            "status": profile.guide_status,
        }

    @staticmethod
    def update_profile(
        db: Session,
        user_id: uuid.UUID,
        profile_in: UserProfileUpdate,
    ) -> Optional[UserProfile]:
        """Update a user profile and invalidate dependent analyses."""
        profile = ProfileService.get_or_create_profile(db, user_id)
        update_data = profile_in.model_dump(exclude_unset=True)

        has_changes = any(getattr(profile, field) != value for field, value in update_data.items())
        if not has_changes:
            return profile

        try:
            for field, value in update_data.items():
                setattr(profile, field, value)

            ProfileService.invalidate_dependencies(db, user_id, profile)
            profile_repo.save(db, db_obj=profile)
            return profile
        except Exception:
            logger.exception("Profile update failed for user %s", user_id)
            db.rollback()
            raise

    @staticmethod
    def invalidate_dependencies(db: Session, user_id: uuid.UUID, profile: UserProfile) -> None:
        """Mark dependent records as outdated after profile changes."""
        idea_repo.mark_scores_outdated(db, user_id, commit=False)
        profile.personalization_profile = None
