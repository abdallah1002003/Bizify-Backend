from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import BusinessRoadmap, RoadmapStage
from app.models.enums import RoadmapStageStatus, StageType
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class BusinessRoadmapService(BaseService):
    """Service for managing Business Roadmaps and their Stages."""

    def _recalculate_roadmap_completion(self, roadmap_id: UUID) -> None:
        stages = self.db.query(RoadmapStage).filter(RoadmapStage.roadmap_id == roadmap_id).all()
        if not stages:
            return

        completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
        completion = (completed / len(stages)) * 100.0

        roadmap = self.db.query(BusinessRoadmap).filter(BusinessRoadmap.id == roadmap_id).first()
        if roadmap is None:
            return

        roadmap.completion_percentage = completion
        self.db.commit()

    # ----------------------------
    # BusinessRoadmap
    # ----------------------------

    def get_roadmap(self, business_id: UUID) -> Optional[BusinessRoadmap]:
        return self.db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == business_id).first()

    def get_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        return self.db.query(BusinessRoadmap).filter(BusinessRoadmap.id == id).first()

    def get_business_roadmaps(self, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
        return self.db.query(BusinessRoadmap).offset(skip).limit(limit).all()

    def init_default_roadmap(self, business_id: UUID) -> BusinessRoadmap:
        existing = self.get_roadmap(business_id=business_id)
        if existing is not None:
            return existing

        db_obj = BusinessRoadmap(business_id=business_id, completion_percentage=0.0)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # Default first stage.
        self.add_roadmap_stage(db_obj.id, StageType.READINESS, 0)
        return db_obj

    def create_business_roadmap(self, obj_in: Any) -> BusinessRoadmap:
        db_obj = BusinessRoadmap(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_business_roadmap(self, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        db_obj = self.get_business_roadmap(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    # ----------------------------
    # RoadmapStage
    # ----------------------------

    def get_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        return self.db.query(RoadmapStage).filter(RoadmapStage.id == id).first()

    def get_roadmap_stages(
        self,
        roadmap_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RoadmapStage]:
        query = self.db.query(RoadmapStage)
        if roadmap_id is not None:
            query = query.filter(RoadmapStage.roadmap_id == roadmap_id)
        return query.order_by(RoadmapStage.order_index.asc()).offset(skip).limit(limit).all()

    def add_roadmap_stage(self, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
        db_stage = RoadmapStage(
            roadmap_id=roadmap_id,
            stage_type=stage_type,
            order_index=order_index,
            status=RoadmapStageStatus.PLANNED,
        )
        self.db.add(db_stage)
        self.db.commit()
        self.db.refresh(db_stage)
        return db_stage

    def create_roadmap_stage(self, obj_in: Any) -> RoadmapStage:
        db_obj = RoadmapStage(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_roadmap_stage(self, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        if db_obj.status == RoadmapStageStatus.COMPLETED:
            self._recalculate_roadmap_completion(db_obj.roadmap_id)

        return db_obj

    def delete_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        db_obj = self.get_roadmap_stage(id=id)
        if not db_obj:
            return None

        roadmap_id = db_obj.roadmap_id
        self.db.delete(db_obj)
        self.db.commit()
        self._recalculate_roadmap_completion(roadmap_id)
        return db_obj

    def transition_stage(self, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
        db_stage = self.get_roadmap_stage(id=stage_id)
        if db_stage is None:
            return None

        if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
            prev_stage = (
                self.db.query(RoadmapStage)
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

        self.db.commit()
        self.db.refresh(db_stage)

        if new_status == RoadmapStageStatus.COMPLETED:
            self._recalculate_roadmap_completion(db_stage.roadmap_id)

        return db_stage

    @staticmethod
    async def handle_business_event(event_type: str, payload: Dict[str, Any]):
        """Async handler for business events."""
        business = payload.get("business")
        if not business:
            return

        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            service = BusinessRoadmapService(db)
            service.init_default_roadmap(business.id)
            logger.info(f"Automatically initialized roadmap for business {business.id} via event {event_type}")
        except Exception as e:
            logger.error(f"Failed to auto-init roadmap via event handler: {e}")
        finally:
            db.close()

def register_business_roadmap_handlers():
    """Register BusinessRoadmapService handlers."""
    dispatcher.subscribe("business.created", BusinessRoadmapService.handle_business_event)


def get_business_roadmap_service(db: Session = Depends(get_db)) -> BusinessRoadmapService:
    return BusinessRoadmapService(db)

# Legacy aliases
def get_roadmap(db: Session, business_id: UUID) -> Optional[BusinessRoadmap]:
    return BusinessRoadmapService(db).get_roadmap(business_id)

def init_default_roadmap(db: Session, business_id: UUID) -> BusinessRoadmap:
    return BusinessRoadmapService(db).init_default_roadmap(business_id)
