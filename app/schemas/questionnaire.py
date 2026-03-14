from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from app.models.user_profile import GuideStatus


class InterestSelection(BaseModel):

    interests: List[str] = Field(..., min_length=1)


class BackgroundContext(BaseModel):

    experience_level: str
    business_context: str
    budget_range: Optional[str] = None
    goals: List[str] = []


class PersonalityAssessment(BaseModel):

     ratings: Dict[str, int]


class QuestionnaireSummary(BaseModel):
    interests: List[str]
    background: Dict[str, Any]
    personality_traits: Dict[str, Any]
    personalization_profile: str
    onboarding_completed: bool

class GuideStatusUpdate(BaseModel):
    status: GuideStatus