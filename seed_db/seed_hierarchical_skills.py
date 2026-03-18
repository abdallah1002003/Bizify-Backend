from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.industry import Industry
from app.models.skill_benchmark import SkillBenchmark


def seed_hierarchy() -> None:
    """
    Seeds the database with hierarchical industries and associated skill benchmarks.
    """
    db: Session = SessionLocal()
    
    try:
        # Clear existing data to avoid conflicts
        db.query(SkillBenchmark).delete()
        db.query(Industry).delete()
        db.commit()

        # Level 0: General Entrepreneurship
        general = Industry(name = "General", level = 0)
        
        db.add(general)
        db.flush()

        # Level 1: Categories
        tech = Industry(name = "Technology", parent_id = general.id, level = 1)
        retail = Industry(name = "Retail", parent_id = general.id, level = 1)
        
        db.add_all([tech, retail])
        db.flush()

        # Level 2: Specific Niches
        ai = Industry(name = "Artificial Intelligence", parent_id = tech.id, level = 2)
        saas = Industry(name = "SaaS", parent_id = tech.id, level = 2)
        
        db.add_all([ai, saas])
        db.flush()

        # Add Benchmarks at different levels
        benchmarks = [
            SkillBenchmark(
                skill_name = "Financial Management", 
                industry_id = general.id, 
                minimum_required_level = 3, 
                weight = 2.0
            ),
            SkillBenchmark(
                skill_name = "Team Leadership", 
                industry_id = general.id, 
                minimum_required_level = 3, 
                weight = 1.5
            ),
            SkillBenchmark(
                skill_name = "Digital Marketing", 
                industry_id = tech.id, 
                minimum_required_level = 4, 
                weight = 2.0
            ),
            SkillBenchmark(
                skill_name = "Product Management", 
                industry_id = tech.id, 
                minimum_required_level = 4, 
                weight = 1.8
            ),
            SkillBenchmark(
                skill_name = "Data Science", 
                industry_id = ai.id, 
                minimum_required_level = 5, 
                weight = 2.0
            ),
            SkillBenchmark(
                skill_name = "Python Programming", 
                industry_id = ai.id, 
                minimum_required_level = 4, 
                weight = 1.5
            ),
        ]
        
        db.add_all(benchmarks)
        db.commit()
        
        print("✅ Successfully seeded hierarchical industry and skills!")

    except Exception as e:
        print(f"❌ Error seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_hierarchy()
