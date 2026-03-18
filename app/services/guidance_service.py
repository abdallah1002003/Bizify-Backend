import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.feature_concept_mapping import FeatureConceptMapping
from app.models.guidance_concept import GuidanceConcept
from app.models.guidance_stage import GuidanceStage
from app.models.user_concept_state import UserConceptState


logger = logging.getLogger(__name__)



class GuidanceService:
    """
    Business Guidance System service.
    Handles stage/concept retrieval, user progress tracking, and feature mapping.
    """

    @staticmethod
    def get_all_stages(db: Session) -> List[GuidanceStage]:
        """
        Retrieves all stages sorted by their sequence order.
        """
        return db.query(GuidanceStage).order_by(GuidanceStage.sequence_order.asc()).all()

    @staticmethod
    def get_concepts_by_stage(db: Session, stage_id: uuid.UUID) -> List[GuidanceConcept]:
        """
        Retrieves all concepts for a specific stage.
        """
        concepts = db.query(GuidanceConcept).filter(
            GuidanceConcept.stage_id == stage_id
        ).order_by(GuidanceConcept.sequence_order.asc()).all()
        
        if not concepts:
            logger.warning(f"No concepts found for stage: {stage_id}")
            
        return concepts

    @staticmethod
    def get_concept_detail(db: Session, concept_id: uuid.UUID) -> GuidanceConcept:
        """
        Retrieves the details of a specific concept.
        """
        concept = db.query(GuidanceConcept).filter(GuidanceConcept.id == concept_id).first()
        
        if not concept:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "The business concept was not found"
            )
            
        return concept

    @staticmethod
    def update_user_progress(
        db: Session, 
        user_id: uuid.UUID, 
        concept_id: uuid.UUID
    ) -> UserConceptState:
        """
        Updates the user's progress by setting the last viewed concept.
        """
        GuidanceService.get_concept_detail(db, concept_id)
        
        state = db.query(UserConceptState).filter(UserConceptState.user_id == user_id).first()
        
        if state:
            state.last_viewed_concept_id = concept_id
        else:
            state = UserConceptState(user_id = user_id, last_viewed_concept_id = concept_id)
            db.add(state)
            
        db.commit()
        db.refresh(state)
        
        return state

    @staticmethod
    def get_user_progress(db: Session, user_id: uuid.UUID) -> Optional[UserConceptState]:
        """
        Retrieves the last point the user reached in the guidance system.
        """
        return db.query(UserConceptState).filter(UserConceptState.user_id == user_id).first()

    @staticmethod
    def get_concept_by_feature(db: Session, feature_key: str) -> Optional[GuidanceConcept]:
        """
        Retrieves the concept associated with a specific feature key.
        """
        mapping = db.query(FeatureConceptMapping).filter(
            FeatureConceptMapping.feature_key == feature_key
        ).first()
        
        if mapping:
            return GuidanceService.get_concept_detail(db, mapping.concept_id)
            
        return None
