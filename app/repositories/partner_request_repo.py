import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.partner_profile import PartnerProfile
from app.models.partner_request import PartnerRequest, RequestStatus
from app.repositories.base import BaseRepository


class PartnerRequestRepository(BaseRepository[PartnerRequest, Any, Any]):
    """Data-access helpers for marketplace partner collaboration requests."""

    def list_for_requester(
        self,
        db: Session,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PartnerRequest]:
        return (
            db.query(self.model)
            .options(
                joinedload(PartnerRequest.partner).joinedload(PartnerProfile.user),
            )
            .filter(self.model.requested_by == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(min(limit, 200))
            .all()
        )

    def get_pending_for_business_and_partner(
        self,
        db: Session,
        *,
        business_id: uuid.UUID,
        partner_profile_id: uuid.UUID,
    ) -> Optional[PartnerRequest]:
        return (
            db.query(self.model)
            .filter(
                self.model.business_id == business_id,
                self.model.partner_id == partner_profile_id,
                self.model.status == RequestStatus.PENDING,
            )
            .first()
        )


partner_request_repo = PartnerRequestRepository(PartnerRequest)
