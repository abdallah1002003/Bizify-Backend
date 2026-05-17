import uuid

from sqlalchemy.orm import Session

from app.models.usage import Usage

# Default limit for AI requests per user if no record exists yet
AI_REQUEST_DEFAULT_LIMIT = 100
AI_REQUEST_RESOURCE_TYPE = "ai_requests"


class UsageRepository:
    """Data-access helpers for `Usage` records."""

    def get_or_create(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Fetch the AI usage record for a user, creating one if it doesn't exist."""
        record = (
            db.query(Usage)
            .filter(
                Usage.user_id == user_id,
                Usage.resource_type == AI_REQUEST_RESOURCE_TYPE,
            )
            .first()
        )
        if record is None:
            record = Usage(
                user_id=user_id,
                resource_type=AI_REQUEST_RESOURCE_TYPE,
                used=0,
                limit_value=AI_REQUEST_DEFAULT_LIMIT,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record

    def increment(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Increment the AI usage counter for a user by 1."""
        record = self.get_or_create(db, user_id)
        record.used = (record.used or 0) + 1
        db.commit()
        db.refresh(record)
        return record

    def check_limit(self, db: Session, user_id: uuid.UUID) -> tuple[bool, Usage]:
        """
        Check whether the user is within their AI usage limit.
        Returns (is_within_limit, usage_record).
        """
        record = self.get_or_create(db, user_id)
        limit = record.limit_value or AI_REQUEST_DEFAULT_LIMIT
        within_limit = (record.used or 0) < limit
        return within_limit, record

    def reset(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Reset the usage counter to zero (useful for billing cycles)."""
        record = self.get_or_create(db, user_id)
        record.used = 0
        db.commit()
        db.refresh(record)
        return record


usage_repo = UsageRepository()
