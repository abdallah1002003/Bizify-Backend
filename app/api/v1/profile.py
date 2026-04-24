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
from app.schemas.skill_gap import PredefinedSkillSearchResult, SkillCategoryRead, UserSkillCreate, UserSkillRead
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



@router.get(
    "/skill-categories",
    response_model=List[SkillCategoryRead],
    summary="List Skill Categories",
    description="Returns all skill categories with their predefined skills. "
                "Use this to build the skill-picker UI.",
)
def list_skill_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SkillCategoryRead]:
    """Return all categories so the frontend can render a grouped skill picker."""
    return SkillGapService.get_all_categories(db)


@router.get(
    "/skills/search",
    response_model=List[PredefinedSkillSearchResult],
    summary="Search Skills",
    description=(
        "Search across all predefined skills by name. "
        "Returns up to 20 results. Useful for building a search box.\n\n"
        "**Example:** `/skills/search?q=python`"
    ),
)
def search_skills(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PredefinedSkillSearchResult]:
    """Full-text search on predefined skill names (case-insensitive)."""
    return SkillGapService.search_predefined_skills(db, q)



@router.get("/skills", response_model=List[UserSkillRead])
def get_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[UserSkillRead]:
    """Return all skills selected by the current user."""
    return SkillGapService.get_user_skills(db, current_user.id)


@router.post(
    "/skills",
    response_model=UserSkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a Skill",
    description=(
        "Add a skill to your profile.\n\n"
        "**Option 1 – pick from the list:** send `predefined_skill_id` only.\n\n"
        "**Option 2 – custom skill:** send `skill_name` only (leave `predefined_skill_id` out or null)."
    ),
)
def add_user_skill(
    skill_in: Annotated[
        UserSkillCreate,
        Body(
            openapi_examples={
                "predefined": {
                    "summary": "✅ Add from list (predefined)",
                    "description": "Pick a skill by its ID from the /skill-categories list.",
                    "value": {"predefined_skill_id": "paste-the-skill-uuid-here"},
                },
                "custom": {
                    "summary": "✏️ Add custom skill (not in list)",
                    "description": "If the skill doesn't exist in the list, type its name here.",
                    "value": {"skill_name": "My Custom Skill"},
                },
            }
        ),
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSkillRead:
    """Add a predefined or custom skill to the current user's profile."""
    return SkillGapService.add_user_skill(db, current_user.id, skill_in)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a skill from the current user's profile."""
    SkillGapService.delete_user_skill(db, current_user.id, skill_id)
    return None
