from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models.users.user import RefreshToken

logger = logging.getLogger(__name__)

def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired refresh tokens from the database.
    Returns the number of deleted records.
    """
    try:
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(RefreshToken)
            .filter(RefreshToken.expires_at < now)
            .delete()
        )
        db.commit()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired refresh tokens")
        return deleted
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cleanup expired tokens: {e}")
        return 0
