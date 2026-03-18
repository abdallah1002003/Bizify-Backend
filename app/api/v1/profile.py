from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.questionnaire import (
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse
)
from app.services.profile_service import ProfileService


router = APIRouter()


@router.post("/questionnaire", response_model=QuestionnaireResponse)
def submit_questionnaire(
    answers: List[QuestionnaireAnswer],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consolidated onboarding questionnaire (Dynamic List of Answers).
    """
    return ProfileService.submit_full_questionnaire(db, current_user.id, answers)


@router.post("/skip")
def skip_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Skips the onboarding questionnaire.
    """
    return ProfileService.skip_questionnaire(db, current_user.id)


@router.post("/restart")
def restart_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resets the questionnaire data to start over.
    """
    return ProfileService.restart_questionnaire(db, current_user.id)


@router.post("/complete")
def finalize_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizes the onboarding process and marks the profile as complete.
    """
    return ProfileService.finalize_onboarding(db, current_user.id)


@router.patch("/guide-status")
def update_guide_status(
    status_in: GuideStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the status of the AI guide for the user.
    """
    return ProfileService.update_guide_status(db, current_user.id, status_in)


@router.get("/")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the current user's profile, creating it if it doesn't exist.
    """
    return ProfileService.get_or_create_profile(db, current_user.id)
