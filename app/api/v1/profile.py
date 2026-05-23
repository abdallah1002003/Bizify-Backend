from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.questionnaire import (
    QuestionnaireAnswer,
    QuestionnaireResponse,
)
from app.schemas.user_profile import UserProfileRead
from app.services.profile_service import ProfileService

router = APIRouter()


@router.post("/questionnaire", response_model=QuestionnaireResponse)
def submit_questionnaire(
    answers: list[QuestionnaireAnswer],
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
) -> dict[str, str]:
    """Skip the onboarding questionnaire only."""
    return ProfileService.skip_questionnaire(db, current_user.id)





@router.post("/restart")
def restart_questionnaire(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Reset questionnaire data so the user can start over."""
    return ProfileService.restart_questionnaire(db, current_user.id)


@router.post("/complete")
def finalize_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Mark onboarding as completed."""
    return ProfileService.finalize_onboarding(db, current_user.id)





@router.get("/", response_model=UserProfileRead)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    """Return the current user's profile, creating it if missing."""
    return ProfileService.get_or_create_profile(db, current_user.id)




PREDEFINED_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js",
    "SQL", "NoSQL", "Docker", "Kubernetes", "AWS",
    "Machine Learning", "Data Analysis", "Project Management",
    "Digital Marketing", "Business Development", "UI/UX Design",
    "Mobile Development", "DevOps", "Blockchain", "AI",
]


SKILL_CATEGORIES = [
    "Programming & Development", "Data & Analytics", "Design & UX",
    "Marketing & Sales", "Business & Management", "Finance & Accounting",
    "Operations & Logistics", "Customer Support", "AI & Machine Learning",
]


@router.get("/skill-categories")
def list_skill_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Return predefined skill categories."""
    return SKILL_CATEGORIES


@router.get("/skills")
def list_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return the current user's skills list."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    return profile.skills_json or []


@router.get("/skills/search")
def search_predefined_skills(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Search predefined skills by keyword."""
    if not q:
        return PREDEFINED_SKILLS
    return [s for s in PREDEFINED_SKILLS if q.lower() in s.lower()]


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_user_skill(
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a custom skill for the current user."""
    skill_name = body.get("skill_name") or body.get("name")
    if not skill_name:
        raise HTTPException(status_code=400, detail="skill_name or name is required")

    profile = ProfileService.get_or_create_profile(db, current_user.id)
    skills = list(profile.skills_json or [])
    new_skill = {"id": str(uuid4()), "name": skill_name, "rating": 3}
    skills.append(new_skill)
    profile.skills_json = skills
    db.commit()
    return new_skill


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a skill by its ID."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    skills = profile.skills_json or []
    updated = [s for s in skills if s.get("id") != skill_id]
    if len(updated) == len(skills):
        raise HTTPException(status_code=404, detail="Skill not found")
    profile.skills_json = updated
    db.commit()
    return None


@router.get("/skills/json")
def get_skills_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the raw skills JSON data for the current user."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    return profile.skills_json or {}


@router.post("/skills/json")
def update_skills_json(
    skills: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Save the raw skills JSON data for the current user."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    profile.skills_json = skills
    db.commit()
    return profile.skills_json or {}
