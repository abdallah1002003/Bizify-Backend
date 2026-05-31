import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.partner_profile import PartnerProfile, PartnerType
from app.models.partner_request import PartnerRequest
from app.models.profile_view import ProfileView
from app.models.user import User
from app.repositories.business_repo import business_repo
from app.repositories.partner_repo import partner_repo
from app.repositories.partner_request_repo import partner_request_repo
from app.models.partner_category import PartnerCategory
from app.schemas.marketplace import (
    MarketplacePartnerPublic,
    MarketplacePartnerRequestRead,
    PartnerCategoryRead,
)


class MarketplaceService:
    """Browse approved partners and submit collaboration requests."""

    @staticmethod
    def _to_public(partner: PartnerProfile) -> MarketplacePartnerPublic:
        user = partner.user
        display = (user.full_name if user else None) or partner.company_name
        cat = partner.category_ref
        return MarketplacePartnerPublic(
            id=partner.id,
            partner_type=partner.partner_type,
            company_name=partner.company_name,
            phone_number=partner.phone_number,
            description=partner.description,
            services_json=partner.services_json,
            experience_json=partner.experience_json,
            display_name=display,
            category_id=cat.id if cat else None,
            category_name=cat.name if cat else None,
            linkedin_url=partner.linkedin_url,
            headline=partner.headline,
            about_summary=partner.about_summary,
            skills_json=partner.skills_json,
            country=partner.country,
            documents_json=partner.documents_json,
            whatsapp=partner.whatsapp,
            email=partner.email,
            website=partner.website,
            facebook_url=partner.facebook_url,
            facebook_followers=partner.facebook_followers,
            instagram_url=partner.instagram_url,
            tiktok_url=partner.tiktok_url,
            google_maps_url=partner.google_maps_url,
            google_rating=partner.google_rating,
            review_count=partner.review_count,
            address=partner.address,
            area=partner.area,
            city=partner.city,
            governorate=partner.governorate,
            industry=partner.industry,
            business_model=partner.business_model,
            minimum_order_quantity=partner.minimum_order_quantity,
            delivery_available=partner.delivery_available,
            estimated_size=partner.estimated_size,
            factory_name=partner.factory_name,
            factory_address=partner.factory_address,
            factory_area=partner.factory_area,
            production_capacity=partner.production_capacity,
            private_label_available=partner.private_label_available,
            exporting=partner.exporting,
            year_founded=partner.year_founded,
            employee_count=partner.employee_count,
            verification_score=partner.verification_score,
            last_verified_date=partner.last_verified_date,
            industry_tags=partner.industry_tags,
            product_tags=partner.product_tags,
            products=partner.products,
            brands_distributed=partner.brands_distributed,
            distribution_areas=partner.distribution_areas,
            manufacturing_capabilities=partner.manufacturing_capabilities,
            certifications=partner.certifications,
            export_countries=partner.export_countries,
            source_urls=partner.source_urls,
        )

    @staticmethod
    def list_categories(
        db: Session, *, partner_type: Optional[PartnerType] = None
    ) -> list[PartnerCategoryRead]:
        rows = partner_repo.list_categories(db, partner_type=partner_type)
        return [PartnerCategoryRead.model_validate(r) for r in rows]

    @staticmethod
    def list_partners(
        db: Session,
        *,
        partner_type: Optional[PartnerType] = None,
        category_id: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MarketplacePartnerPublic]:
        rows = partner_repo.list_marketplace_approved(
            db,
            partner_type=partner_type,
            category_id=category_id,
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
    def record_profile_view(
        db: Session,
        *,
        partner_id: uuid.UUID,
        viewer: User,
    ) -> None:
        profile = partner_repo.get_marketplace_by_id(db, partner_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found",
            )
        view = ProfileView(
            partner_id=partner_id,
            viewer_id=viewer.id,
            viewer_name=viewer.full_name,
            viewer_email=viewer.email,
            viewer_role=viewer.role.value if hasattr(viewer.role, "value") else str(viewer.role),
            viewed_at=datetime.utcnow(),
        )
        db.add(view)
        db.commit()

    @staticmethod
    def get_profile_view_stats(
        db: Session,
        *,
        partner_profile_id: uuid.UUID,
        limit: int = 20,
    ) -> dict:
        total = (
            db.query(func.count(ProfileView.id))
            .filter(ProfileView.partner_id == partner_profile_id)
            .scalar()
        ) or 0

        recent = (
            db.query(ProfileView)
            .filter(ProfileView.partner_id == partner_profile_id)
            .order_by(ProfileView.viewed_at.desc())
            .limit(limit)
            .all()
        )

        unique_viewers = (
            db.query(func.count(func.distinct(ProfileView.viewer_id)))
            .filter(
                ProfileView.partner_id == partner_profile_id,
                ProfileView.viewer_id.isnot(None),
            )
            .scalar()
        ) or 0

        return {
            "total_views": total,
            "unique_viewers": unique_viewers,
            "recent_views": [
                {
                    "viewer_name": v.viewer_name,
                    "viewer_email": v.viewer_email,
                    "viewer_role": v.viewer_role,
                    "viewed_at": v.viewed_at.isoformat() if v.viewed_at else None,
                }
                for v in recent
            ],
        }

    @staticmethod
    def list_my_requests(
        db: Session,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MarketplacePartnerRequestRead]:
        rows = partner_request_repo.list_for_requester(
            db, user_id, skip=skip, limit=limit
        )
        out: list[MarketplacePartnerRequestRead] = []
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
