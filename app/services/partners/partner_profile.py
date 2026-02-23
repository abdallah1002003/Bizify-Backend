"""
Partner Profile CRUD operations and matching.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PartnerProfile
from app.models.enums import ApprovalStatus, PartnerType

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# PartnerProfile CRUD
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
    elif hasattr(user_id, "model_dump"):
        data = user_id.model_dump(exclude_unset=True)
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

    profile.approval_status = ApprovalStatus.APPROVED
    profile.approved_by = approver_id
    profile.approved_at = _utc_now()
    db.commit()
    db.refresh(profile)
    return profile


def match_partners_by_capability(db: Session, business_needs: Dict[str, Any]) -> List[PartnerProfile]:
    required_type = business_needs.get("required_type")

    query = db.query(PartnerProfile).filter(PartnerProfile.approval_status == ApprovalStatus.APPROVED)
    if required_type is not None:
        query = query.filter(PartnerProfile.partner_type == required_type)
    return query.all()
