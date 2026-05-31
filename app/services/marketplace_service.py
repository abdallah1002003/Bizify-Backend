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
        d: dict = partner.details_json or {}
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
            # Rich fields unpacked from details_json
            whatsapp=d.get("whatsapp"),
            email=d.get("email"),
            website=d.get("website"),
            facebook_url=d.get("facebook_url"),
            facebook_followers=d.get("facebook_followers"),
            instagram_url=d.get("instagram_url"),
            tiktok_url=d.get("tiktok_url"),
            google_maps_url=d.get("google_maps_url"),
            google_rating=d.get("google_rating"),
            review_count=d.get("review_count"),
            address=d.get("address"),
            area=d.get("area"),
            city=d.get("city"),
            governorate=d.get("governorate"),
            industry=d.get("industry"),
            business_model=d.get("business_model"),
            minimum_order_quantity=d.get("minimum_order_quantity") or d.get("moq"),
            delivery_available=d.get("delivery_available"),
            estimated_size=d.get("estimated_size"),
            factory_name=d.get("factory_name"),
            factory_address=d.get("factory_address"),
            factory_area=d.get("factory_area"),
            production_capacity=d.get("production_capacity"),
            private_label_available=d.get("private_label_available"),
            exporting=d.get("exporting"),
            year_founded=d.get("year_founded"),
            employee_count=d.get("employee_count"),
            verification_score=d.get("verification_score"),
            last_verified_date=d.get("last_verified_date"),
            industry_tags=d.get("industry_tags"),
            product_tags=d.get("product_tags"),
            products=d.get("products"),
            brands_distributed=d.get("brands_distributed"),
            distribution_areas=d.get("distribution_areas"),
            manufacturing_capabilities=d.get("manufacturing_capabilities"),
            certifications=d.get("certifications"),
            export_countries=d.get("export_countries"),
            source_urls=d.get("source_urls"),
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
