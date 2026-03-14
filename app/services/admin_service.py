from sqlalchemy.orm import Session
from app.models.security_log import SecurityLog

class AdminService:
    @staticmethod
    def get_security_logs(db: Session):
        return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).all()
