from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.partners import partner_service


def create_partner_request(db: Session, obj_in):
    return partner_service.create_partner_request(db, obj_in=obj_in)


def accept_partner_request(db: Session, request_id):
    return partner_service.accept_partner_request(db, request_id=request_id)
