import uuid
from typing import Any, List

from sqlalchemy.orm import Session

from app.models.idea import Idea
from app.repositories.base import BaseRepository


class IdeaRepository(BaseRepository[Idea, Any, Any]):
    """Data-access helpers for ideas."""

    def get_by_owner(self, db: Session, user_id: uuid.UUID) -> List[Idea]:
        """Fetch all ideas owned by a specific user."""
        return db.query(self.model).filter(self.model.owner_id == user_id).all()

    def get_by_business(self, db: Session, business_id: uuid.UUID) -> List[Idea]:
        """Fetch all ideas belonging to a specific business."""
        return db.query(self.model).filter(self.model.business_id == business_id).all()

    def get_by_ids_in_business(
        self,
        db: Session,
        idea_ids: List[uuid.UUID],
        business_id: uuid.UUID,
    ) -> List[Idea]:
        """Fetch ideas by IDs within a single business boundary."""
        return (
            db.query(self.model)
            .filter(
                self.model.id.in_(idea_ids),
                self.model.business_id == business_id,
            )
            .all()
        )

    def count_all(self, db: Session) -> int:
        """Return the total number of ideas."""
        return db.query(self.model).count()

    def mark_scores_outdated(self, db: Session, owner_id: uuid.UUID, *, commit: bool = True) -> None:
        """Mark all of a user's ideas for score recalculation."""
        db.query(self.model).filter(self.model.owner_id == owner_id).update(
            {"is_score_outdated": True}
        )
        if commit:
            db.commit()
        else:
            db.flush()


idea_repo = IdeaRepository(Idea)
