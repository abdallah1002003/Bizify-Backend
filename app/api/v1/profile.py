import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from typing import List

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.questionnaire import (
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse
)
from app.schemas.user_profile import UserProfileRead
from app.services.profile_service import ProfileService
from app.schemas.skill_gap import UserSkill, UserSkillCreate
from app.services.skill_gap_service import SkillGapService


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


@router.get("/", response_model = UserProfileRead)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserProfileRead:
    """
    Retrieves the current user's profile, creating it if it doesn't exist.
    """
    return ProfileService.get_or_create_profile(db, current_user.id)


@router.get("/skills", response_model=List[UserSkill])
def get_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all skills for the current user.
    """
    return SkillGapService.get_user_skills(db, current_user.id)


@router.post("/skills", response_model=UserSkill, status_code=status.HTTP_201_CREATED)
def add_user_skill(
    skill_in: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adds a new skill to the user's profile.
    """
    return SkillGapService.add_user_skill(db, current_user.id, skill_in)


@router.put("/skills/{skill_id}", response_model=UserSkill)
def update_user_skill(
    skill_id: uuid.UUID,
    skill_in: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates an existing skill for the current user.
    """
    return SkillGapService.update_user_skill(db, current_user.id, skill_id, skill_in)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific skill from the user's profile.
    """
    SkillGapService.delete_user_skill(db, current_user.id, skill_id)
    return None
