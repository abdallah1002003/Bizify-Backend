from datetime import datetime

from sqlalchemy import Column, DateTime, String

from app.core.database import Base


class TokenBlacklist(Base):
    """
    SQLAlchemy model representing revoked (blacklisted) JWT tokens.
    """
    
    __tablename__ = "token_blacklist"
    
    token = Column(String, primary_key=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
