from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.business import business_service


def create_business_invite(db: Session, obj_in):
    return business_service.create_business_invite(db, obj_in=obj_in)


def update_business_invite(db: Session, db_obj, obj_in):
    return business_service.update_business_invite(db, db_obj=db_obj, obj_in=obj_in)
