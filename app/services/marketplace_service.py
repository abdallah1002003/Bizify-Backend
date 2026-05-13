import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.partner_profile import PartnerProfile, PartnerType
from app.models.partner_request import PartnerRequest
from app.models.user import User
from app.repositories.business_repo import business_repo
from app.repositories.partner_repo import partner_repo
from app.repositories.partner_request_repo import partner_request_repo
from app.schemas.marketplace import (
    MarketplacePartnerPublic,
    MarketplacePartnerRequestRead,
)


class MarketplaceService:
    """Browse approved partners and submit collaboration requests."""

    @staticmethod
    def _to_public(partner: PartnerProfile) -> MarketplacePartnerPublic:
        user = partner.user
        display = (user.full_name if user else None) or partner.company_name
        return MarketplacePartnerPublic(
            id=partner.id,
            partner_type=partner.partner_type,
            company_name=partner.company_name,
            description=partner.description,
            services_json=partner.services_json,
            experience_json=partner.experience_json,
            display_name=display,
        )

    @staticmethod
    def list_partners(
        db: Session,
        *,
        partner_type: Optional[PartnerType] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MarketplacePartnerPublic]:
        rows = partner_repo.list_marketplace_approved(
            db,
            partner_type=partner_type,
            q=q,
            skip=skip,
            limit=limit,
        )
        return [MarketplaceService._to_public(p) for p in rows]

    @staticmethod
    def get_partner(db: Session, partner_id: uuid.UUID) -> MarketplacePartnerPublic:
        profile = partner_repo.get_marketplace_by_id(db, partner_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found or not available in the marketplace",
            )
        return MarketplaceService._to_public(profile)

    @staticmethod
    def create_partner_request(
        db: Session,
        *,
        current_user: User,
        partner_id: uuid.UUID,
        business_id: uuid.UUID,
    ) -> PartnerRequest:
        partner = partner_repo.get_marketplace_by_id(db, partner_id)
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found or not available in the marketplace",
            )

        if partner.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send a request to your own partner profile",
            )

        business = business_repo.get(db, business_id)
        if not business or business.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found or you do not own this business",
            )

        existing = partner_request_repo.get_pending_for_business_and_partner(
            db,
            business_id=business_id,
            partner_profile_id=partner_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pending request already exists for this business and partner",
            )

        return partner_request_repo.create(
            db,
            obj_in={
                "business_id": business_id,
                "partner_id": partner_id,
                "requested_by": current_user.id,
            },
        )

    @staticmethod
    def list_my_requests(
        db: Session,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketplacePartnerRequestRead]:
        rows = partner_request_repo.list_for_requester(
            db, user_id, skip=skip, limit=limit
        )
        out: List[MarketplacePartnerRequestRead] = []
        for row in rows:
            partner_public = None
            if row.partner:
                partner_public = MarketplaceService._to_public(row.partner)
            out.append(
                MarketplacePartnerRequestRead(
                    id=row.id,
                    business_id=row.business_id,
                    partner_id=row.partner_id,
                    requested_by=row.requested_by,
                    status=row.status,
                    created_at=row.created_at,
                    partner=partner_public,
                )
            )
        return out
