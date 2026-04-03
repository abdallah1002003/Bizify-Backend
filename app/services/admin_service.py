from typing import List
from sqlalchemy.orm import Session

from app.models.security_log import SecurityLog
from app.repositories.admin_repo import security_repo


class AdminService:
    """
    Service class for administrative operations.
    Provides methods for log auditing and system-wide management.
    """
    
    @staticmethod
    def get_security_logs(db: Session) -> List[SecurityLog]:
        """
        Retrieves all security logs ordered by creation date descending.
        """
        return security_repo.get_recent_logs(db)
