from typing import List, Optional

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
    choices: List[str]
    label: Optional[str] = None


class UserProfileOutput(BaseModel):
    """
    Structured output for the user's business profile.
    """
    curiosity_domain: Optional[str] = None
    experience_level: Optional[str] = None
    business_interests: List[str] = []
    target_region: Optional[str] = None
    founder_setup: Optional[str] = None
    risk_tolerance: Optional[str] = None


class CareerProfileOutput(BaseModel):
    """
    Structured output for the user's career profile.
    """
    free_day_preferences: List[str] = []
    preferred_work_types: List[str] = []
    problem_solving_styles: List[str] = []
    preferred_work_environments: List[str] = []
    desired_impact: List[str] = []


class QuestionnaireResponse(BaseModel):
    """
    The final structured response matching the user's required JSON output.
    """
    user_profile: UserProfileOutput
    career_profile: CareerProfileOutput
