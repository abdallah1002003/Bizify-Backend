# ruff: noqa
"""
Business Invite and BusinessInviteIdea CRUD operations.
"""
from __future__ import annotations

from datetime import timedelta
import logging
import secrets
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import BusinessInvite, BusinessInviteIdea, User
from app.models.enums import CollaboratorRole, InviteStatus

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# BusinessInvite
# ----------------------------

def get_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    return db.query(BusinessInvite).filter(BusinessInvite.id == id).first()  # type: ignore[no-any-return]


def get_business_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    return get_invite(db, id=id)


def get_invites(db: Session, business_id: UUID) -> List[BusinessInvite]:
    return db.query(BusinessInvite).filter(BusinessInvite.business_id == business_id).all()  # type: ignore[no-any-return]


def get_business_invites(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessInvite]:
    return db.query(BusinessInvite).offset(skip).limit(limit).all()  # type: ignore[no-any-return]


def create_invite(db: Session, business_id: UUID, email: str, invited_by: UUID) -> BusinessInvite:
    db_obj = BusinessInvite(
        business_id=business_id,
        email=email,
        token=secrets.token_urlsafe(32),
        status=InviteStatus.PENDING,
        invited_by=invited_by,
        expires_at=_utc_now() + timedelta(days=7),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_business_invite(db: Session, obj_in: Any) -> BusinessInvite:
    data = _to_update_dict(obj_in)
    data.setdefault("expires_at", _utc_now() + timedelta(days=7))
    db_obj = BusinessInvite(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_business_invite(db: Session, db_obj: BusinessInvite, obj_in: Any) -> BusinessInvite:
    from app.services.business import business_collaborator
    
    before = db_obj.status
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if before != InviteStatus.ACCEPTED and db_obj.status == InviteStatus.ACCEPTED:
        # Keep backward-compatible behavior expected by tests.
        user = db.query(User).filter(User.email == db_obj.email).first()
        if user is not None:
            business_collaborator.add_collaborator(db, db_obj.business_id, user.id, CollaboratorRole.VIEWER)

    return db_obj


def delete_business_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    db_obj = get_business_invite(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def accept_invite(db: Session, token: str, user_id: UUID) -> bool:
    from app.services.business import business_collaborator
    
    invite = db.query(BusinessInvite).filter(BusinessInvite.token == token).first()
    if invite is None:
        return False

    if invite.status != InviteStatus.PENDING:
        return False

    if invite.expires_at < _utc_now():
        invite.status = InviteStatus.EXPIRED
        db.commit()
        return False

    invite.status = InviteStatus.ACCEPTED
    db.commit()
    business_collaborator.add_collaborator(db, invite.business_id, user_id, CollaboratorRole.EDITOR)
    return True


# ----------------------------
# BusinessInviteIdea
# ----------------------------

def get_business_invite_idea(db: Session, id: UUID) -> Optional[BusinessInviteIdea]:
    return db.query(BusinessInviteIdea).filter(BusinessInviteIdea.id == id).first()  # type: ignore[no-any-return]


def get_business_invite_ideas(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessInviteIdea]:
    return db.query(BusinessInviteIdea).offset(skip).limit(limit).all()  # type: ignore[no-any-return]


def create_business_invite_idea(db: Session, obj_in: Any) -> BusinessInviteIdea:
    db_obj = BusinessInviteIdea(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_business_invite_idea(db: Session, db_obj: BusinessInviteIdea, obj_in: Any) -> BusinessInviteIdea:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_business_invite_idea(db: Session, id: UUID) -> Optional[BusinessInviteIdea]:
    db_obj = get_business_invite_idea(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
