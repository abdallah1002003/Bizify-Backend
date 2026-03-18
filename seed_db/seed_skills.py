from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.skill_benchmark import SkillBenchmark
from app.models.user import User
from app.models.user_skill import UserSkill


def seed_data() -> None:
    """
    Seed initial benchmarks and user skills for testing.
    """
    db: Session = SessionLocal()
    
    try:
        # Fetch the debug user
        user_email = "abdallah.antar.mday@gmail.com"
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            print(f"User {user_email} not found. Please create it first.")
            return

        # Add Benchmarks (The Standard)
        benchmarks = [
            SkillBenchmark(
                skill_name = "Financial Management", 
                min_required_level = 4, 
                weight = 1.5
            ),
            SkillBenchmark(
                skill_name = "Digital Marketing", 
                min_required_level = 3, 
                weight = 1.0
            ),
            SkillBenchmark(
                skill_name = "Market Research", 
                min_required_level = 4, 
                weight = 1.2
            ),
            SkillBenchmark(
                skill_name = "Sales Strategy", 
                min_required_level = 3, 
                weight = 1.1
            )
        ]
        
        for bench in benchmarks:
            existing = db.query(SkillBenchmark).filter(
                SkillBenchmark.skill_name == bench.skill_name
            ).first()
            
            if not existing:
                db.add(bench)

        # Add User Skills (Your current level)
        user_skills = [
            UserSkill(user_id = user.id, skill_name = "Financial Management", rating = 2),
            UserSkill(user_id = user.id, skill_name = "Digital Marketing", rating = 4),
            UserSkill(user_id = user.id, skill_name = "Market Research", rating = 1)
        ]
        
        # Clear old skills to prevent primary key issues if re-running
        db.query(UserSkill).filter(UserSkill.user_id == user.id).delete()
        db.add_all(user_skills)

        db.commit()
        
        print("✅ Success: Benchmarks and User Skills seeded!")
        print(f"Go to Swagger and call /api/v1/skills/analyze for {user_email}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
