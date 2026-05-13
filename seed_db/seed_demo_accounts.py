import asyncio
import json
import uuid

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.questionnaire_storage import merge_questionnaire

async def create_demo_users():
    db = SessionLocal()
    
    # Check if they exist, if so delete them to re-create
    existing = db.query(User).filter(User.email.in_(["creative@bizify.com", "tech@bizify.com"])).all()
    for e in existing:
        db.delete(e)
    db.commit()

    user_creative = User(
        email="creative@bizify.com",
        password_hash=get_password_hash("demo123"),
        full_name="Creative Demo",
        is_active=True
    )
    db.add(user_creative)
    
    user_tech = User(
        email="tech@bizify.com",
        password_hash=get_password_hash("demo123"),
        full_name="Tech Demo",
        is_active=True
    )
    db.add(user_tech)
    
    db.commit()
    db.refresh(user_creative)
    db.refresh(user_tech)

    profile_creative = UserProfile(
        user_id=user_creative.id,
        questionnaire_json={
            "user_profile": {
                "curiosity_domain": "Art&Design",
                "experience_level": "Growth-Seeker",
                "business_interests": ["E-commerce", "Marketplace"],
                "target_region": "Global",
                "founder_setup": "Co-founder",
                "risk_tolerance": "I enjoy taking calculated risks",
            },
            "career_profile": {
                "free_day_preferences": ["Design or express ideas"],
                "preferred_work_types": ["Creative work (design, writing, media)"],
                "problem_solving_styles": ["Creative challenges"],
                "preferred_work_environments": ["Creative studio"],
                "desired_impact": ["Innovate new ideas"],
            },
            "interests": ["E-commerce", "Marketplace"],
        },
    )
    db.add(profile_creative)
    
    profile_tech = UserProfile(
        user_id=user_tech.id,
        questionnaire_json={
            "user_profile": {
                "curiosity_domain": "Technology",
                "experience_level": "Aspiring Entrepreneur",
                "business_interests": ["SaaS", "AI"],
                "target_region": "MENA",
                "founder_setup": "Solo",
                "risk_tolerance": "High risk tolerance",
            },
            "career_profile": {
                "free_day_preferences": ["Code or build systems"],
                "preferred_work_types": ["Technical architecture"],
                "problem_solving_styles": ["Logical puzzles"],
                "preferred_work_environments": ["Remote"],
                "desired_impact": ["Change the world with tech"],
            },
            "interests": ["SaaS", "AI"],
        },
    )
    db.add(profile_tech)
    
    db.commit()
    print("Demo accounts created.")
    
    # Now run the AI pipeline for both
    from app.services.ai_pipeline_service import AIPipelineService
    import httpx
    
    print("\nRunning AI Pipeline for Creative Demo...")
    try:
        res = await AIPipelineService.run(db, user_creative.id)
        print(f"Creative AI trigger: {res}")
        
        print("Running AI Pipeline for Tech Demo...")
        res2 = await AIPipelineService.run(db, user_tech.id)
        print(f"Tech AI trigger: {res2}")
        
        print("\nWaiting 20 seconds for AI to generate (polling)...")
        for _ in range(4):
            print("...")
            await asyncio.sleep(5)
            
        print("Fetching results for Creative...")
        creative_results = await AIPipelineService.get_results(user_creative.id)
        profile_creative.questionnaire_json = merge_questionnaire(
            profile_creative.questionnaire_json,
            personalization_profile=json.dumps(creative_results),
        )
        
        print("Fetching results for Tech...")
        tech_results = await AIPipelineService.get_results(user_tech.id)
        profile_tech.questionnaire_json = merge_questionnaire(
            profile_tech.questionnaire_json,
            personalization_profile=json.dumps(tech_results),
        )
        
        db.commit()
        print("\nAll done! Demo accounts are fully seeded with AI data.")
    except Exception as e:
        print(f"Error during AI pipeline: {e}")
        db.rollback()
    
    db.close()

if __name__ == "__main__":
    asyncio.run(create_demo_users())
