from typing import Optional

from pydantic import BaseModel

from app.models.user_profile import GuideStatus


class GuideStatusUpdate(BaseModel):
    """
    Pydantic model for updating the user onboarding guide status.
    """
    
    status: GuideStatus


class QuestionnaireAnswer(BaseModel):
    """
    Pydantic model for a single questionnaire answer from the frontend.
    """
    
    field: str
    question: Optional[str] = None
    multi: bool = False
    choices: list[str]
    label: Optional[str] = None


class UserProfileOutput(BaseModel):
    """
    Structured output for the user's business profile.
    """
    curiosity_domain: Optional[str] = None
    experience_level: Optional[str] = None
    business_interests: list[str] = []
    target_region: Optional[str] = None
    founder_setup: Optional[str] = None
    risk_tolerance: Optional[str] = None


class CareerProfileOutput(BaseModel):
    """
    Structured output for the user's career profile.
    """
    free_day_preferences: list[str] = []
    preferred_work_types: list[str] = []
    problem_solving_styles: list[str] = []
    preferred_work_environments: list[str] = []
    desired_impact: list[str] = []


class QuestionnaireResponse(BaseModel):
    """
    The final structured response matching the user's required JSON output.
    """
    user_profile: UserProfileOutput
    career_profile: CareerProfileOutput
