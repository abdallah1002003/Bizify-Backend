import uuid
from typing import Any, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.repositories.base import BaseRepository


class PartnerRepository(BaseRepository[PartnerProfile, Any, Any]):
    """Data-access helpers for partner profiles."""

    def get_by_user_id(self, db: Session, user_id: uuid.UUID) -> Optional[PartnerProfile]:
        """Fetch the partner profile for a specific user."""
        return db.query(self.model).filter(self.model.user_id == user_id).first()

    def get_by_profile_id(self, db: Session, profile_id: uuid.UUID) -> Optional[PartnerProfile]:
        """Fetch a partner profile by its primary key."""
        return db.query(self.model).filter(self.model.id == profile_id).first()

    def get_filtered(
        self,
        db: Session,
        status: Optional[ApprovalStatus] = None,
    ) -> List[PartnerProfile]:
        """List partner profiles, optionally filtered by approval status."""
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
        """Return only approved partner profiles."""
        return self.get_filtered(db, status=ApprovalStatus.APPROVED)

    def list_marketplace_approved(
        self,
        db: Session,
        *,
        partner_type: Optional[PartnerType] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[PartnerProfile]:
        """List approved partner profiles for marketplace browse/search."""
        query = (
            db.query(self.model)
            .options(joinedload(PartnerProfile.user))
            .filter(self.model.approval_status == ApprovalStatus.APPROVED)
        )
        if partner_type is not None:
            query = query.filter(self.model.partner_type == partner_type)
        if q:
            term = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    self.model.company_name.ilike(term),
                    self.model.description.ilike(term),
                )
            )
        return (
            query.order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(min(limit, 100))
            .all()
        )

    def get_marketplace_by_id(
        self, db: Session, profile_id: uuid.UUID
    ) -> Optional[PartnerProfile]:
        """Return a partner profile by id only if approved (for public marketplace detail)."""
        return (
            db.query(self.model)
            .options(joinedload(PartnerProfile.user))
            .filter(
                self.model.id == profile_id,
                self.model.approval_status == ApprovalStatus.APPROVED,
            )
            .first()
        )


partner_repo = PartnerRepository(PartnerProfile)
