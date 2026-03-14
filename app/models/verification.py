from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime, timedelta, timezone
import enum

class VerificationType(enum.Enum):
    ACCOUNT_VERIFICATION = "account_verification"
    PASSWORD_RESET = "password_reset"

class AccountVerification(Base):
    __tablename__ = "account_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    otp_code = Column(String(6), nullable=False) 
    user = relationship("User", backref="verification_codes")
    verification_type = Column(Enum(VerificationType), default=VerificationType.ACCOUNT_VERIFICATION)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="verification_codes")   

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            return now.replace(tzinfo=None) > self.expires_at
        return now > self.expires_at