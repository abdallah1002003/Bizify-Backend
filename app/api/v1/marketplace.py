from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.partner_profile import PartnerType
from app.models.user import User
from app.schemas.marketplace import (
    MarketplacePartnerPublic,
    MarketplacePartnerRequestCreate,
    MarketplacePartnerRequestRead,
    PartnerCategoryRead,
)
from app.services.marketplace_service import MarketplaceService

router = APIRouter()


@router.get(
    "/categories",
    response_model=list[PartnerCategoryRead],
    summary="List partner categories",
)
def list_categories(
    partner_type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[PartnerCategoryRead]:
    partner_type = _parse_partner_type(partner_type_filter) if partner_type_filter else None
    return MarketplaceService.list_categories(db, partner_type=partner_type)


def _parse_partner_type(type_param: Optional[str]) -> Optional[PartnerType]:
    if type_param is None or type_param.strip() == "":
        return None
    try:
        return PartnerType(type_param.strip().upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type; use MENTOR, SUPPLIER, or MANUFACTURER",
        ) from exc


@router.get(
    "/partners",
    response_model=list[MarketplacePartnerPublic],
    summary="List marketplace partners",
    description=(
        "Returns admin-approved partner profiles for browse/search. "
        "This is separate from partner registration (`/users/register-partner`)."
    ),
)
def list_marketplace_partners(
    partner_type_filter: Optional[str] = Query(
        None,
        alias="type",
        description="Filter by partner type: MENTOR, SUPPLIER, or MANUFACTURER",
    ),
    category_id: Optional[UUID] = Query(None, description="Filter by category UUID"),
    q: Optional[str] = Query(
        None,
        description="Search in company name and description (case-insensitive)",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[MarketplacePartnerPublic]:
    partner_type = _parse_partner_type(partner_type_filter)
    return MarketplaceService.list_partners(
        db, partner_type=partner_type, category_id=category_id, q=q, skip=skip, limit=limit
    )


@router.get(
    "/partners/{partner_id}",
    response_model=MarketplacePartnerPublic,
    summary="Get marketplace partner by id",
)
def get_marketplace_partner(
    partner_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> MarketplacePartnerPublic:
    return MarketplaceService.get_partner(db, partner_id)


@router.post(
    "/partners/{partner_id}/requests",
    response_model=MarketplacePartnerRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Request collaboration with a partner",
)
def create_marketplace_partner_request(
    partner_id: UUID,
    body: MarketplacePartnerRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketplacePartnerRequestRead:
    row = MarketplaceService.create_partner_request(
        db,
        current_user=current_user,
        partner_id=partner_id,
        business_id=body.business_id,
    )
    partner_public = MarketplaceService.get_partner(db, partner_id)
    return MarketplacePartnerRequestRead(
        id=row.id,
        business_id=row.business_id,
        partner_id=row.partner_id,
        requested_by=row.requested_by,
        status=row.status,
        created_at=row.created_at,
        partner=partner_public,
    )


@router.post(
    "/partners/{partner_id}/views",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record a profile view",
)
def record_profile_view(
    partner_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    MarketplaceService.record_profile_view(db, partner_id=partner_id, viewer=current_user)


@router.get(
    "/my-profile/views",
    summary="Get profile view stats for the logged-in partner",
)
def get_my_profile_view_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.repositories.partner_repo import partner_repo as _partner_repo
    profile = _partner_repo.get_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No partner profile found for this user",
        )
    return MarketplaceService.get_profile_view_stats(db, partner_profile_id=profile.id)


@router.get(
    "/requests",
    response_model=list[MarketplacePartnerRequestRead],
    summary="List my marketplace requests",
)
def list_my_marketplace_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MarketplacePartnerRequestRead]:
    return MarketplaceService.list_my_requests(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
