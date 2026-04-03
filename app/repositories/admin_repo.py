import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.security_log import SecurityLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog, Any, Any]):
    """
    Repository for tracking user account actions (Audit Logs).
    """

    def log_action(self, db: Session, user_id: uuid.UUID, action: str, ip_address: Optional[str] = None) -> AuditLog:
        """Log a specific user action like password change or deletion."""
        log = AuditLog(user_id=user_id, action=action, ip_address=ip_address)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log


class SecurityRepository(BaseRepository[SecurityLog, Any, Any]):
    """
    Repository for tracking system security events.
    """

    def get_recent_logs(self, db: Session) -> List[SecurityLog]:
        """Fetch all security logs, newest first."""
        return db.query(self.model).order_by(self.model.created_at.desc()).all()

    def log_event(
        self,
        db: Session,
        *,
        user_id: Optional[uuid.UUID],
        event_type: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> SecurityLog:
        return self.create(
            db,
            obj_in={
                "user_id": user_id,
                "event_type": event_type,
                "details": details,
                "ip_address": ip_address,
            },
        )


audit_repo = AuditRepository(AuditLog)
security_repo = SecurityRepository(SecurityLog)
