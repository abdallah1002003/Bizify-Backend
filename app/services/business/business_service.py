from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    Business,
    BusinessCollaborator,
    BusinessInvite,
    BusinessInviteIdea,
    BusinessRoadmap,
    RoadmapStage,
    User,
)
from app.models.enums import (
    BusinessStage,
    CollaboratorRole,
    InviteStatus,
    RoadmapStageStatus,
    StageType,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return obj_in.model_dump(exclude_unset=True)
    return dict(obj_in)


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return db_obj


# ----------------------------
# Business
# ----------------------------

def get_business(db: Session, id: UUID) -> Optional[Business]:
    return db.query(Business).filter(Business.id == id).first()


def get_businesses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[Business]:
    query = db.query(Business)
    if owner_id is not None:
        query = query.filter(Business.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()


def create_business(db: Session, obj_in: Any) -> Business:
    db_obj = Business(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Ensure roadmap exists.
    if not get_roadmap(db, business_id=db_obj.id):
        init_default_roadmap(db, db_obj.id)

    # Ensure owner collaborator exists.
    owner_collab = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == db_obj.id,
            BusinessCollaborator.user_id == db_obj.owner_id,
        )
        .first()
    )
    if owner_collab is None:
        add_collaborator(db, db_obj.id, db_obj.owner_id, CollaboratorRole.OWNER)

    return db_obj


def update_business(db: Session, db_obj: Business, obj_in: Any) -> Business:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_business(db: Session, id: UUID) -> Optional[Business]:
    db_obj = get_business(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def update_business_stage(db: Session, business_id: UUID, new_stage: BusinessStage) -> Optional[Business]:
    db_obj = get_business(db, business_id)
    if db_obj is None:
        return None
    db_obj.stage = new_stage
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ----------------------------
# BusinessRoadmap
# ----------------------------

def get_roadmap(db: Session, business_id: UUID) -> Optional[BusinessRoadmap]:
    return db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == business_id).first()


def get_business_roadmap(db: Session, id: UUID) -> Optional[BusinessRoadmap]:
    return db.query(BusinessRoadmap).filter(BusinessRoadmap.id == id).first()


def get_business_roadmaps(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
    return db.query(BusinessRoadmap).offset(skip).limit(limit).all()


def init_default_roadmap(db: Session, business_id: UUID) -> BusinessRoadmap:
    existing = get_roadmap(db, business_id=business_id)
    if existing is not None:
        return existing

    db_obj = BusinessRoadmap(business_id=business_id, completion_percentage=0.0)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Default first stage.
    add_roadmap_stage(db, db_obj.id, StageType.READINESS, 0)
    return db_obj


def create_business_roadmap(db: Session, obj_in: Any) -> BusinessRoadmap:
    db_obj = BusinessRoadmap(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_business_roadmap(db: Session, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_business_roadmap(db: Session, id: UUID) -> Optional[BusinessRoadmap]:
    db_obj = get_business_roadmap(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# RoadmapStage
# ----------------------------

def get_roadmap_stage(db: Session, id: UUID) -> Optional[RoadmapStage]:
    return db.query(RoadmapStage).filter(RoadmapStage.id == id).first()


def get_roadmap_stages(
    db: Session,
    roadmap_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[RoadmapStage]:
    query = db.query(RoadmapStage)
    if roadmap_id is not None:
        query = query.filter(RoadmapStage.roadmap_id == roadmap_id)
    return query.order_by(RoadmapStage.order_index.asc()).offset(skip).limit(limit).all()


def add_roadmap_stage(db: Session, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
    db_stage = RoadmapStage(
        roadmap_id=roadmap_id,
        stage_type=stage_type,
        order_index=order_index,
        status=RoadmapStageStatus.PLANNED,
    )
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    return db_stage


def create_roadmap_stage(db: Session, obj_in: Any) -> RoadmapStage:
    db_obj = RoadmapStage(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_roadmap_stage(db: Session, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if db_obj.status == RoadmapStageStatus.COMPLETED:
        _recalculate_roadmap_completion(db, db_obj.roadmap_id)

    return db_obj


def delete_roadmap_stage(db: Session, id: UUID) -> Optional[RoadmapStage]:
    db_obj = get_roadmap_stage(db, id=id)
    if not db_obj:
        return None

    roadmap_id = db_obj.roadmap_id
    db.delete(db_obj)
    db.commit()
    _recalculate_roadmap_completion(db, roadmap_id)
    return db_obj


def transition_stage(db: Session, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    db_stage = get_roadmap_stage(db, id=stage_id)
    if db_stage is None:
        return None

    if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
        prev_stage = (
            db.query(RoadmapStage)
            .filter(
                RoadmapStage.roadmap_id == db_stage.roadmap_id,
                RoadmapStage.order_index == db_stage.order_index - 1,
            )
            .first()
        )
        if prev_stage and prev_stage.status != RoadmapStageStatus.COMPLETED:
            raise ValueError("Prerequisite stage not completed")

    db_stage.status = new_status
    if new_status == RoadmapStageStatus.COMPLETED:
        db_stage.completed_at = _utc_now()

    db.commit()
    db.refresh(db_stage)

    if new_status == RoadmapStageStatus.COMPLETED:
        _recalculate_roadmap_completion(db, db_stage.roadmap_id)

    return db_stage


def update_stage_status(db: Session, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    """Backward-compatible alias used by older tests/services."""
    return transition_stage(db, stage_id=stage_id, new_status=new_status)


def _recalculate_roadmap_completion(db: Session, roadmap_id: UUID) -> None:
    stages = db.query(RoadmapStage).filter(RoadmapStage.roadmap_id == roadmap_id).all()
    if not stages:
        return

    completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
    completion = (completed / len(stages)) * 100.0

    roadmap = db.query(BusinessRoadmap).filter(BusinessRoadmap.id == roadmap_id).first()
    if roadmap is None:
        return

    roadmap.completion_percentage = completion
    db.commit()


# ----------------------------
# BusinessCollaborator
# ----------------------------

def get_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    return db.query(BusinessCollaborator).filter(BusinessCollaborator.id == id).first()


def get_business_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    return get_collaborator(db, id=id)


def get_collaborators(db: Session, business_id: UUID) -> List[BusinessCollaborator]:
    return db.query(BusinessCollaborator).filter(BusinessCollaborator.business_id == business_id).all()


def get_business_collaborators(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessCollaborator]:
    return db.query(BusinessCollaborator).offset(skip).limit(limit).all()


def add_collaborator(
    db: Session,
    business_id: UUID,
    user_id: UUID,
    role: CollaboratorRole,
) -> BusinessCollaborator:
    existing = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id,
        )
        .first()
    )
    if existing is not None:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    db_obj = BusinessCollaborator(business_id=business_id, user_id=user_id, role=role)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_business_collaborator(db: Session, obj_in: Any) -> BusinessCollaborator:
    data = _to_update_dict(obj_in)
    return add_collaborator(
        db,
        business_id=data["business_id"],
        user_id=data["user_id"],
        role=data["role"],
    )


def update_business_collaborator(db: Session, db_obj: BusinessCollaborator, obj_in: Any) -> BusinessCollaborator:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_collaborator(db: Session, business_id: UUID, user_id: UUID) -> None:
    db_obj = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id,
        )
        .first()
    )
    if db_obj is None:
        return

    if db_obj.role == CollaboratorRole.OWNER:
        raise PermissionError("Cannot remove owner collaborator")

    db.delete(db_obj)
    db.commit()


def delete_business_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    db_obj = get_business_collaborator(db, id=id)
    if not db_obj:
        return None

    if db_obj.role == CollaboratorRole.OWNER:
        raise PermissionError("Cannot remove owner collaborator")

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# BusinessInvite
# ----------------------------

def get_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    return db.query(BusinessInvite).filter(BusinessInvite.id == id).first()


def get_business_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    return get_invite(db, id=id)


def get_invites(db: Session, business_id: UUID) -> List[BusinessInvite]:
    return db.query(BusinessInvite).filter(BusinessInvite.business_id == business_id).all()


def get_business_invites(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessInvite]:
    return db.query(BusinessInvite).offset(skip).limit(limit).all()


def create_invite(db: Session, business_id: UUID, email: str, invited_by: UUID) -> BusinessInvite:
    import secrets

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
    before = db_obj.status
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if before != InviteStatus.ACCEPTED and db_obj.status == InviteStatus.ACCEPTED:
        # Keep backward-compatible behavior expected by tests.
        user = db.query(User).filter(User.email == db_obj.email).first()
        if user is not None:
            add_collaborator(db, db_obj.business_id, user.id, CollaboratorRole.VIEWER)

    return db_obj


def delete_business_invite(db: Session, id: UUID) -> Optional[BusinessInvite]:
    db_obj = get_business_invite(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def accept_invite(db: Session, token: str, user_id: UUID) -> bool:
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
    add_collaborator(db, invite.business_id, user_id, CollaboratorRole.EDITOR)
    return True


# ----------------------------
# BusinessInviteIdea
# ----------------------------

def get_business_invite_idea(db: Session, id: UUID) -> Optional[BusinessInviteIdea]:
    return db.query(BusinessInviteIdea).filter(BusinessInviteIdea.id == id).first()


def get_business_invite_ideas(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessInviteIdea]:
    return db.query(BusinessInviteIdea).offset(skip).limit(limit).all()


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


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "business_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("business_service reset_internal_state called")
