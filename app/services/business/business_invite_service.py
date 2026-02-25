# type: ignore
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.business import business_invite


def create_business_invite(db: Session, obj_in):
    return business_invite.create_business_invite(db, obj_in=obj_in)


def update_business_invite(db: Session, db_obj, obj_in):
    return business_invite.update_business_invite(db, db_obj=db_obj, obj_in=obj_in)
