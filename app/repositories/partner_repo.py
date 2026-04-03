import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.partner_profile import ApprovalStatus, PartnerProfile
from app.repositories.base import BaseRepository


class PartnerRepository(BaseRepository[PartnerProfile, Any, Any]):
    """
    Repository for PartnerProfile-specific database operations.
    """

    def get_by_user_id(self, db: Session, user_id: uuid.UUID) -> Optional[PartnerProfile]:
        """Fetch the partner profile for a specific user."""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .first()
        )

    def get_by_profile_id(self, db: Session, profile_id: uuid.UUID) -> Optional[PartnerProfile]:
        """Fetch a partner profile by its primary key."""
        return db.query(self.model).filter(self.model.id == profile_id).first()

    def get_filtered(
        self, db: Session, status: Optional[ApprovalStatus] = None
    ) -> List[PartnerProfile]:
        """
        List all partner profiles, with an optional filter by approval status.
        Used by admin dashboards to review pending, approved, or rejected applications.
        """
        query = db.query(self.model)
        if status:
            query = query.filter(self.model.approval_status == status)
        return query.all()

    def get_all(self, db: Session) -> List[PartnerProfile]:
        """Return all partner profiles regardless of status."""
        return self.get_filtered(db)

    def get_pending(self, db: Session) -> List[PartnerProfile]:
        """Return only profiles awaiting admin review."""
        return self.get_filtered(db, status=ApprovalStatus.PENDING)

    def get_approved(self, db: Session) -> List[PartnerProfile]:
        """Return only approved and active partner profiles."""
        return self.get_filtered(db, status=ApprovalStatus.APPROVED)


partner_repo = PartnerRepository(PartnerProfile)
