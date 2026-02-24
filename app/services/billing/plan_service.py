"""
Billing Plan CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.models import Plan
from app.db.database import get_db
from app.services.base_service import BaseService
from app.services.billing.crud_utils import get_by_id, list_records
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class PlanService(BaseService):
    """Service for managing Billing Plans."""

    def get_plan(self, id: UUID) -> Optional[Plan]:
        """Return a single plan by id."""
        return get_by_id(self.db, Plan, id)

    def get_plans(self, skip: int = 0, limit: int = 100) -> List[Plan]:
        """Return paginated plan records."""
        return list_records(self.db, Plan, skip=skip, limit=limit)

    def create_plan(self, obj_in: Any) -> Plan:
        """Create a new billing plan."""
        db_obj = Plan(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_plan(self, db_obj: Plan, obj_in: Any) -> Plan:
        """Update mutable fields on an existing plan."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_plan(self, id: UUID) -> Optional[Plan]:
        """Delete a plan by id and return the deleted record."""
        db_obj = self.get_plan(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    """Dependency provider for PlanService."""
    return PlanService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

def get_plan(db: Session, id: UUID) -> Optional[Plan]:
    return PlanService(db).get_plan(id)


def get_plans(db: Session, skip: int = 0, limit: int = 100) -> List[Plan]:
    return PlanService(db).get_plans(skip, limit)


def create_plan(db: Session, obj_in: Any) -> Plan:
    return PlanService(db).create_plan(obj_in)


def update_plan(db: Session, db_obj: Plan, obj_in: Any) -> Plan:
    return PlanService(db).update_plan(db_obj, obj_in)


def delete_plan(db: Session, id: UUID) -> Optional[Plan]:
    return PlanService(db).delete_plan(id)
