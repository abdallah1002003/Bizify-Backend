from typing import Annotated, Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.questionnaire import (
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse,
)
from app.schemas.user_profile import UserProfileRead
from app.services.profile_service import ProfileService

router = APIRouter()


@router.post("/questionnaire", response_model=QuestionnaireResponse)
def submit_questionnaire(
    answers: List[QuestionnaireAnswer],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionnaireResponse:
    """Submit the onboarding questionnaire."""
    return ProfileService.submit_full_questionnaire(db, current_user.id, answers)


@router.get("/questionnaire")
def get_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the user's saved questionnaire JSON data."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    return profile.questionnaire_json or {}


@router.post("/skip")
def skip_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Skip the onboarding questionnaire only."""
    return ProfileService.skip_questionnaire(db, current_user.id)





@router.post("/restart")
def restart_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Reset questionnaire data so the user can start over."""
    return ProfileService.restart_questionnaire(db, current_user.id)


@router.post("/complete")
def finalize_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Mark onboarding as completed."""
    return ProfileService.finalize_onboarding(db, current_user.id)





@router.get("/", response_model=UserProfileRead)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    """Return the current user's profile, creating it if missing."""
    return ProfileService.get_or_create_profile(db, current_user.id)




@router.post("/skills/json")
def update_skills_json(
    skills: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Save the raw skills JSON data for the current user."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    profile.skills_json = skills
    db.commit()
    return profile.skills_json or {}
