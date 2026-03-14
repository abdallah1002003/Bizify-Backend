from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from datetime import datetime

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    token = Column(String, primary_key=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
