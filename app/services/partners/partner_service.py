from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PartnerProfile, PartnerRequest
from app.models.enums import ApprovalStatus, PartnerType, RequestStatus

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# PartnerProfile
# ----------------------------

def get_partner_profile(db: Session, id: UUID) -> Optional[PartnerProfile]:
    return db.query(PartnerProfile).filter(PartnerProfile.id == id).first()


def get_partner_profiles(db: Session, skip: int = 0, limit: int = 100) -> List[PartnerProfile]:
    return db.query(PartnerProfile).offset(skip).limit(limit).all()


def create_partner_profile(
    db: Session,
    user_id: Optional[UUID] = None,
    partner_type: Optional[PartnerType] = None,
    bio: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    obj_in: Any = None,
) -> PartnerProfile:
    if obj_in is not None:
        data = _to_update_dict(obj_in)
    elif user_id is not None and hasattr(user_id, "model_dump"):
        # This handles the case where a schema is passed as the first positional arg
        data = cast(Any, user_id).model_dump(exclude_unset=True)
    else:
        data = {
            "user_id": user_id,
            "partner_type": partner_type,
            "description": bio,
            "services_json": details or {},
            "approval_status": ApprovalStatus.PENDING,
        }

    if not data.get("approval_status"):
        data["approval_status"] = ApprovalStatus.PENDING

    db_obj = PartnerProfile(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_partner_profile(db: Session, db_obj: PartnerProfile, obj_in: Any) -> PartnerProfile:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_partner_profile(db: Session, id: UUID) -> Optional[PartnerProfile]:
    db_obj = get_partner_profile(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def approve_partner_profile(db: Session, profile_id: UUID, approver_id: UUID) -> Optional[PartnerProfile]:
    profile = get_partner_profile(db, profile_id)
    if profile is None:
        return None

    profile.approval_status = ApprovalStatus.APPROVED  # type: ignore[assignment]
    profile.approved_by = approver_id  # type: ignore[assignment]
    profile.approved_at = _utc_now()  # type: ignore[assignment]
    db.commit()
    db.refresh(profile)
    return profile


def match_partners_by_capability(db: Session, business_needs: Dict[str, Any]) -> List[PartnerProfile]:
    required_type = business_needs.get("required_type")

    query = db.query(PartnerProfile).filter(PartnerProfile.approval_status == ApprovalStatus.APPROVED)
    if required_type is not None:
        query = query.filter(PartnerProfile.partner_type == required_type)
    return query.all()


# ----------------------------
# PartnerRequest
# ----------------------------

def get_partner_request(db: Session, id: UUID) -> Optional[PartnerRequest]:
    return db.query(PartnerRequest).filter(PartnerRequest.id == id).first()


def get_partner_requests(db: Session, skip: int = 0, limit: int = 100) -> List[PartnerRequest]:
    return db.query(PartnerRequest).offset(skip).limit(limit).all()


def submit_partner_request(
    db: Session,
    business_id: UUID,
    partner_id: UUID,
    request_type: Optional[str] = None,
    context: Optional[str] = None,
    requested_by: Optional[UUID] = None,
) -> PartnerRequest:
    _ = request_type
    _ = context
    db_obj = PartnerRequest(
        business_id=business_id,
        partner_id=partner_id,
        requested_by=requested_by,
        status=RequestStatus.PENDING,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_partner_request(db: Session, obj_in: Any) -> PartnerRequest:
    data = _to_update_dict(obj_in)
    db_obj = PartnerRequest(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_partner_request(db: Session, db_obj: PartnerRequest, obj_in: Any) -> PartnerRequest:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_partner_request(db: Session, id: UUID) -> Optional[PartnerRequest]:
    db_obj = get_partner_request(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def transition_request_status(
    db: Session,
    request_id: UUID,
    new_status: RequestStatus,
    performer_id: Optional[UUID] = None,
) -> Optional[PartnerRequest]:
    _ = performer_id
    request = get_partner_request(db, request_id)
    if request is None:
        return None

    request.status = new_status
    db.commit()
    db.refresh(request)
    return request


def accept_partner_request(db: Session, request_id: UUID) -> Optional[PartnerRequest]:
    return transition_request_status(db, request_id, RequestStatus.ACCEPTED)


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "partner_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("partner_service reset_internal_state called")
