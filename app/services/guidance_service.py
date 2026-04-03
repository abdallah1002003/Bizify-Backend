import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.guidance_concept import GuidanceConcept
from app.models.guidance_stage import GuidanceStage
from app.models.user_concept_state import UserConceptState
from app.repositories.guidance_repo import guidance_repo


logger = logging.getLogger(__name__)


class GuidanceService:
    """
    Business Guidance System service.
    All DB queries are delegated to guidance_repo.
    This service only contains business logic (e.g. 404 validation, logging).
    """

    @staticmethod
    def get_all_stages(db: Session) -> List[GuidanceStage]:
        """Return all guidance stages sorted by sequence order."""
        return guidance_repo.get_all_stages(db)

    @staticmethod
    def get_concepts_by_stage(db: Session, stage_id: uuid.UUID) -> List[GuidanceConcept]:
        """Return all concepts for a stage. Logs a warning if the stage is empty."""
        concepts = guidance_repo.get_concepts_by_stage(db, stage_id)
        if not concepts:
            logger.warning(f"No concepts found for stage: {stage_id}")
        return concepts

    @staticmethod
    def get_concept_detail(db: Session, concept_id: uuid.UUID) -> GuidanceConcept:
        """
        Fetch a concept by ID.
        Business rule: raises 404 if the concept does not exist.
        """
        concept = guidance_repo.get_concept_by_id(db, concept_id)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The business concept was not found",
            )
        return concept

    @staticmethod
    def update_user_progress(
        db: Session, user_id: uuid.UUID, concept_id: uuid.UUID
    ) -> UserConceptState:
        """
        Mark a concept as the user's latest progress point.
        Validates the concept exists before saving (delegates upsert to repo).
        """
        # Business rule: validate the concept exists first
        GuidanceService.get_concept_detail(db, concept_id)
        return guidance_repo.upsert_user_progress(db, user_id, concept_id)

    @staticmethod
    def get_user_progress(db: Session, user_id: uuid.UUID) -> Optional[UserConceptState]:
        """Return the user's last viewed concept (their progress bookmark)."""
        return guidance_repo.get_user_progress(db, user_id)

    @staticmethod
    def get_concept_by_feature(db: Session, feature_key: str) -> Optional[GuidanceConcept]:
        """
        Return the concept linked to a UI feature key.
        Powers the Contextual In-App Help (? button) without exposing DB logic to the API layer.
        """
        return guidance_repo.get_concept_by_feature_key(db, feature_key)
