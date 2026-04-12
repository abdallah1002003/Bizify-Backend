from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.questionnaire import (
    GuideStatusUpdate,
    QuestionnaireAnswer,
    QuestionnaireResponse,
)
from app.schemas.skill_gap import UserSkill, UserSkillCreate
from app.schemas.user_profile import UserProfileRead
from app.services.profile_service import ProfileService
from app.services.skill_gap_service import SkillGapService

router = APIRouter()


@router.post("/questionnaire", response_model=QuestionnaireResponse)
def submit_questionnaire(
    answers: List[QuestionnaireAnswer],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionnaireResponse:
    """Submit the onboarding questionnaire."""
    return ProfileService.submit_full_questionnaire(db, current_user.id, answers)


@router.post("/skip")
def skip_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Skip the onboarding questionnaire only."""
    return ProfileService.skip_questionnaire(db, current_user.id)


@router.post("/skip-guide")
def skip_guide(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Skip the beginner guide only."""
    return ProfileService.skip_guide(db, current_user.id)


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


@router.patch("/guide-status")
def update_guide_status(
    status_in: GuideStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update the current user's guide status."""
    return ProfileService.update_guide_status(db, current_user.id, status_in)


@router.get("/", response_model=UserProfileRead)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    """Return the current user's profile, creating it if missing."""
    return ProfileService.get_or_create_profile(db, current_user.id)


@router.get("/skills", response_model=List[UserSkill])
def get_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[UserSkill]:
    """Return all skills for the current user."""
    return SkillGapService.get_user_skills(db, current_user.id)


@router.post("/skills", response_model=UserSkill, status_code=status.HTTP_201_CREATED)
def add_user_skill(
    skill_in: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSkill:
    """Add a new skill to the user's profile."""
    return SkillGapService.add_user_skill(db, current_user.id, skill_in)


@router.put("/skills/{skill_id}", response_model=UserSkill)
def update_user_skill(
    skill_id: UUID,
    skill_in: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSkill:
    """Update an existing user skill."""
    return SkillGapService.update_user_skill(db, current_user.id, skill_id, skill_in)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a skill from the current user's profile."""
    SkillGapService.delete_user_skill(db, current_user.id, skill_id)
    return None
