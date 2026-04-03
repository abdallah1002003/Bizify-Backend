import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.feature_concept_mapping import FeatureConceptMapping
from app.models.guidance_concept import GuidanceConcept
from app.models.guidance_stage import GuidanceStage
from app.models.user_concept_state import UserConceptState
from app.repositories.base import BaseRepository


class GuidanceRepository(BaseRepository[GuidanceStage, Any, Any]):
    """
    Repository for the Business Guidance System.
    Covers: GuidanceStage, GuidanceConcept, UserConceptState, FeatureConceptMapping.
    """

    def get_all_stages(self, db: Session) -> List[GuidanceStage]:
        """Return all guidance stages sorted by their defined sequence order."""
        return (
            db.query(GuidanceStage)
            .order_by(GuidanceStage.sequence_order.asc())
            .all()
        )

    def get_concepts_by_stage(
        self, db: Session, stage_id: uuid.UUID
    ) -> List[GuidanceConcept]:
        """Return all concepts for a given stage, in sequence order."""
        return (
            db.query(GuidanceConcept)
            .filter(GuidanceConcept.stage_id == stage_id)
            .order_by(GuidanceConcept.sequence_order.asc())
            .all()
        )

    def get_concept_by_id(
        self, db: Session, concept_id: uuid.UUID
    ) -> Optional[GuidanceConcept]:
        """Fetch a single concept by its ID."""
        return (
            db.query(GuidanceConcept)
            .filter(GuidanceConcept.id == concept_id)
            .first()
        )

    def get_user_progress(
        self, db: Session, user_id: uuid.UUID
    ) -> Optional[UserConceptState]:
        """Fetch the last concept a user viewed (their progress bookmark)."""
        return (
            db.query(UserConceptState)
            .filter(UserConceptState.user_id == user_id)
            .first()
        )

    def upsert_user_progress(
        self, db: Session, user_id: uuid.UUID, concept_id: uuid.UUID
    ) -> UserConceptState:
        """
        Update the user's progress bookmark to the given concept.
        Creates the record if it does not yet exist (upsert pattern).
        """
        state = self.get_user_progress(db, user_id)
        if state:
            state.last_viewed_concept_id = concept_id
        else:
            state = UserConceptState(
                user_id=user_id, last_viewed_concept_id=concept_id
            )
            db.add(state)
        db.commit()
        db.refresh(state)
        return state

    def get_concept_by_feature_key(
        self, db: Session, feature_key: str
    ) -> Optional[GuidanceConcept]:
        """
        Fetch the concept linked to a UI feature key.
        Powers the Contextual In-App Help system (the ? button next to features).
        """
        mapping = (
            db.query(FeatureConceptMapping)
            .filter(FeatureConceptMapping.feature_key == feature_key)
            .first()
        )
        if mapping:
            return self.get_concept_by_id(db, mapping.concept_id)
        return None


guidance_repo = GuidanceRepository(GuidanceStage)
