import uuid

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.feature_concept_mapping import FeatureConceptMapping
from app.models.guidance_concept import GuidanceConcept
from app.models.guidance_stage import GuidanceStage


def seed_data() -> None:
    """
    Seeds the database with initial guidance stages, concepts, and feature mappings.
    """
    db: Session = SessionLocal()
    
    try:
        # Create Stages
        stage1 = GuidanceStage(
            id = uuid.uuid4(),
            name = "Stage 1",
            description = "Stage 1 description",
            sequence_order = 1
        )
        stage2 = GuidanceStage(
            id = uuid.uuid4(),
            name = "Stage 2",
            description = "Stage 2 description",
            sequence_order = 2
        )
        
        db.add_all([stage1, stage2])
        db.commit()
        
        # Create Concepts for Stage 1
        concept1 = GuidanceConcept(
            id = uuid.uuid4(),
            stage_id = stage1.id,
            title = "Concept 1",
            concept_explanation = "Concept 1 explanation",
            platform_support_explanation = "Concept 1 platform support explanation",
            sequence_order = 1
        )
        concept2 = GuidanceConcept(
            id = uuid.uuid4(),
            stage_id = stage1.id,
            title = "Concept 2",
            concept_explanation = "Concept 2 explanation",
            platform_support_explanation = "Concept 2 platform support explanation",
            sequence_order = 2
        )
        
        db.add_all([concept1, concept2])
        db.commit()

        # Feature Mapping (Example for Teams)
        mapping = FeatureConceptMapping(
            feature_key = "teams_page",
            concept_id = concept2.id
        )
        
        db.add(mapping)
        db.commit()

        print("✅ Data seeded successfully!")
        print(f"Stages added: {stage1.name}, {stage2.name}")
        
    except Exception as e:
        print(f"❌ Error occurred while seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
