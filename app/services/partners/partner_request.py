# ruff: noqa
"""
Partner Request CRUD operations and status transitions.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PartnerRequest
from app.models.enums import RequestStatus

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# PartnerRequest CRUD
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

    request.status = new_status  # type: ignore
    db.commit()
    db.refresh(request)
    return request


def accept_partner_request(db: Session, request_id: UUID) -> Optional[PartnerRequest]:
    return transition_request_status(db, request_id, RequestStatus.ACCEPTED)
