from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.partners import partner_service


def create_partner_profile(db: Session, obj_in):
    return partner_service.create_partner_profile(db, obj_in=obj_in)


def approve_partner_profile(db: Session, profile_id, approver_id):
    return partner_service.approve_partner_profile(db, profile_id=profile_id, approver_id=approver_id)
