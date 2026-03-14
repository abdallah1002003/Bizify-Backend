from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.profile_service import ProfileService
from app.schemas.questionnaire import (
    InterestSelection, BackgroundContext, PersonalityAssessment , GuideStatusUpdate
)

router = APIRouter()

@router.post("/interests")
def step1_interests(interests_in: InterestSelection, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.update_interests(db, current_user.id, interests_in)

@router.post("/background")
def step2_background(background_in: BackgroundContext, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.update_background(db, current_user.id, background_in)

@router.post("/personality")
def step3_personality(personality_in: PersonalityAssessment, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.update_personality(db, current_user.id, personality_in)

@router.post("/complete")
def finalize_onboarding(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.finalize_onboarding(db, current_user.id)

@router.patch("/guide-status")
def update_guide_status(status_in: GuideStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.update_guide_status(db, current_user.id, status_in)

@router.get("/")
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProfileService.get_or_create_profile(db, current_user.id)
