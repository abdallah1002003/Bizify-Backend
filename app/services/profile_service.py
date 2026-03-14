from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from app.schemas.questionnaire import (
    InterestSelection, BackgroundContext, 
    PersonalityAssessment , GuideStatusUpdate
)
from fastapi import HTTPException

class ProfileService:
    @staticmethod
    def get_or_create_profile(db: Session, user_id: str) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_interests(db: Session, user_id: str, interests_in: InterestSelection):
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.interests_json = interests_in.interests
        db.commit()
        return {"message": "Interests saved successfully", "interests": profile.interests_json}

    @staticmethod
    def update_background(db: Session, user_id: str, background_in: BackgroundContext):
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.background_json = background_in.model_dump()
        db.commit()
        return {"message": "Background saved successfully", "background": profile.background_json}

    @staticmethod
    def update_personality(db: Session, user_id: str, personality_in: PersonalityAssessment):
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.personality_json = personality_in.ratings
        db.commit()
        return {"message": "Personality saved successfully", "personality": profile.personality_json}

    @staticmethod
    def finalize_onboarding(db: Session, user_id: str):
        profile = ProfileService.get_or_create_profile(db, user_id)
        if not profile.interests_json or not profile.background_json or not profile.personality_json:
            raise HTTPException(status_code=400, detail="Please complete all steps first")
        
        interests_text = ", ".join(profile.interests_json)
        exp = profile.background_json.get("experience_level", "N/A")
        summary = f"User interested in {interests_text} with {exp} experience level."
        
        profile.personalization_profile = summary
        profile.onboarding_completed = True
        db.commit()
        return {"status": "success", "personalization_summary": summary}

    @staticmethod
    def update_guide_status(db: Session, user_id: str, status_in: GuideStatusUpdate):
        profile = ProfileService.get_or_create_profile(db, user_id)
        profile.guide_status = status_in.status
        db.commit()
        return {"message": "Guide status updated successfully", "status": profile.guide_status}
