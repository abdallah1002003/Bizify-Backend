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




# Maps each category to its predefined skills pool
CATEGORY_SKILLS: dict[str, list[str]] = {
    "Programming & Development": [
        "Python", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
        "Node.js", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "REST APIs", "GraphQL",
        "Docker", "Kubernetes", "AWS", "Azure", "Git", "CI/CD",
        "Mobile Development", "iOS Development", "Android Development",
        "DevOps", "Microservices", "System Design", "Blockchain",
    ],
    "Data & Analytics": [
        "Data Analysis", "SQL", "Python", "R", "Excel", "Power BI", "Tableau",
        "Data Visualization", "Statistics", "ETL", "Big Data", "Apache Spark",
        "Data Engineering", "Business Intelligence", "A/B Testing", "Google Analytics",
    ],
    "Design & UX": [
        "UI/UX Design", "Figma", "Adobe XD", "Photoshop", "Illustrator",
        "User Research", "Wireframing", "Prototyping", "Brand Design",
        "Graphic Design", "Motion Design", "Design Systems", "Product Design",
    ],
    "Marketing & Sales": [
        "Digital Marketing", "SEO", "SEM", "Google Ads", "Social Media Marketing",
        "Content Marketing", "Email Marketing", "Copywriting", "Brand Strategy",
        "Sales", "CRM", "HubSpot", "Lead Generation", "Growth Hacking",
        "Affiliate Marketing", "Market Research",
    ],
    "Business & Management": [
        "Business Development", "Project Management", "Product Management",
        "Strategy", "Business Analysis", "Agile", "Scrum", "Operations Management",
        "Change Management", "Leadership", "Negotiation", "Stakeholder Management",
        "Business Planning",
    ],
    "Finance & Accounting": [
        "Financial Analysis", "Accounting", "Bookkeeping", "Financial Modeling",
        "Excel", "QuickBooks", "Budgeting", "Forecasting", "Taxation",
        "Auditing", "Investment Analysis", "Valuation", "Cash Flow Management",
        "Financial Reporting", "Risk Management",
    ],
    "Operations & Logistics": [
        "Supply Chain Management", "Logistics", "Inventory Management",
        "Process Improvement", "Lean", "Six Sigma", "Quality Assurance",
        "Procurement", "Vendor Management", "ERP Systems", "SAP",
        "Warehouse Management",
    ],
    "Customer Support": [
        "Customer Service", "CRM", "Zendesk", "Intercom", "Technical Support",
        "Client Relations", "Communication", "Problem Solving",
        "Conflict Resolution", "Salesforce", "Customer Success", "Account Management",
    ],
    "AI & Machine Learning": [
        "Machine Learning", "Deep Learning", "Neural Networks", "NLP",
        "Computer Vision", "TensorFlow", "PyTorch", "Scikit-learn",
        "Data Science", "AI", "LLMs", "Prompt Engineering", "MLOps",
        "Reinforcement Learning", "Statistical Modeling", "Python",
    ],
}

# Flat deduplicated list for global search (no category filter)
PREDEFINED_SKILLS: list[str] = sorted(
    {skill for skills in CATEGORY_SKILLS.values() for skill in skills}
)

SKILL_CATEGORIES: list[str] = list(CATEGORY_SKILLS.keys())


@router.get("/skill-categories")
def list_skill_categories(
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
    category: str = "",
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Search predefined skills by keyword, optionally filtered by category."""
    pool = CATEGORY_SKILLS.get(category, PREDEFINED_SKILLS) if category else PREDEFINED_SKILLS
    if not q:
        return pool
    return [s for s in pool if q.lower() in s.lower()]


@router.get("/skills/json")
def get_skills_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return the raw skills JSON data for the current user."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    return profile.skills_json or []


@router.post("/skills/json")
def update_skills_json(
    skills: list[dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Save the raw skills JSON data for the current user."""
    profile = ProfileService.get_or_create_profile(db, current_user.id)
    profile.skills_json = skills
    db.commit()
    return profile.skills_json or []


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_user_skill(
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a skill for the current user."""
    skill_name = body.get("skill_name") or body.get("name")
    if not skill_name:
        raise HTTPException(status_code=400, detail="skill_name or name is required")

    profile = ProfileService.get_or_create_profile(db, current_user.id)
    skills = list(profile.skills_json or [])
    new_skill = {"id": str(uuid4()), "name": str(skill_name), "rating": 3}
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
