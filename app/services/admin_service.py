import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.security_log import SecurityLog
from app.models.user import User
from app.repositories.admin_repo import audit_repo, security_repo
from app.repositories.idea_repo import idea_repo
from app.repositories.user_repo import user_repo


class AdminService:
    """Administrative workflows for logs, stats, and user moderation."""

    @staticmethod
    def get_security_logs(db: Session) -> List[SecurityLog]:
        """Fetch security logs ordered by newest first."""
        return security_repo.get_recent_logs(db)

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Return aggregate statistics for the admin dashboard."""
        try:
            return {
                "total_users": user_repo.count_all(db),
                "suspended_users": user_repo.count_inactive(db),
                "total_ideas": idea_repo.count_all(db),
                "status": "online",
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Failed to fetch statistics") from exc

    @staticmethod
    def suspend_user(db: Session, admin_id: uuid.UUID, user_id: uuid.UUID) -> User:
        """Suspend a user and record the action in the audit log."""
        user = user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="User is already suspended")

        try:
            user = user_repo.update(
                db,
                db_obj=user,
                obj_in={
                    "is_active": False,
                    "revoked_at": datetime.now(timezone.utc),
                },
                commit=False,
                refresh=False,
            )
            audit_repo.log_action(
                db=db,
                user_id=admin_id,
                action=f"SUSPENDED_USER_{user_id}",
                commit=False,
            )
            db.commit()
            db.refresh(user)
            return user
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to suspend user and record audit log",
            ) from exc
