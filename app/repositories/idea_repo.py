import uuid
from typing import Any, List

from sqlalchemy.orm import Session

from app.models.idea import Idea
from app.repositories.base import BaseRepository


class IdeaRepository(BaseRepository[Idea, Any, Any]):
    """
    Repository for Idea-specific database operations.
    """

    def get_by_owner(self, db: Session, user_id: uuid.UUID) -> List[Idea]:
        """Fetch all ideas owned by a specific user."""
        return db.query(self.model).filter(self.model.owner_id == user_id).all()

    def get_by_business(self, db: Session, business_id: uuid.UUID) -> List[Idea]:
        """Fetch all ideas belonging to a specific business."""
        return db.query(self.model).filter(self.model.business_id == business_id).all()

    def get_by_ids_in_business(
        self, db: Session, idea_ids: List[uuid.UUID], business_id: uuid.UUID
    ) -> List[Idea]:
        """
        Fetch ideas by a list of IDs, filtered to a specific business.
        Used to prevent cross-business data leakage when assigning ideas to team members.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.id.in_(idea_ids),
                self.model.business_id == business_id,
            )
            .all()
        )

    def mark_scores_outdated(self, db: Session, owner_id: uuid.UUID, *, commit: bool = True) -> None:
        """
        Mark all ideas of a user as score-outdated.
        Called when the user's profile changes significantly (e.g., experience level update),
        so the AI re-evaluates the ideas against the new profile.
        """
        db.query(self.model).filter(self.model.owner_id == owner_id).update(
            {"is_score_outdated": True}
        )
        if commit:
            db.commit()
        else:
            db.flush()


idea_repo = IdeaRepository(Idea)
