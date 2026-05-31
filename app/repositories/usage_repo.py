import uuid

from sqlalchemy.orm import Session

from app.models.usage import Usage

AI_TOKEN_RESOURCE_TYPE = "ai_tokens"

# Default token budget for users with no active plan (matches Free plan)
AI_TOKEN_DEFAULT_LIMIT = 20_000

# Tokens reserved per PPF section purchase (one section = 3 K tokens)
PPF_TOKENS_PER_SECTION = 3_000


class UsageRepository:
    """Data-access helpers for `Usage` records (token-based)."""

    def get_or_create(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Fetch the AI token usage record for a user, creating one if absent."""
        record = (
            db.query(Usage)
            .filter(
                Usage.user_id == user_id,
                Usage.resource_type == AI_TOKEN_RESOURCE_TYPE,
            )
            .first()
        )
        if record is None:
            record = Usage(
                user_id=user_id,
                resource_type=AI_TOKEN_RESOURCE_TYPE,
                used=0,
                limit_value=AI_TOKEN_DEFAULT_LIMIT,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record

    def add_tokens(self, db: Session, user_id: uuid.UUID, tokens: int) -> Usage:
        """Add `tokens` to the user's accumulated token usage."""
        record = self.get_or_create(db, user_id)
        record.used = (record.used or 0) + max(tokens, 0)
        db.commit()
        db.refresh(record)
        return record

    def check_limit(self, db: Session, user_id: uuid.UUID) -> tuple[bool, Usage]:
        """
        Check whether the user is within their token limit.
        Returns (is_within_limit, usage_record).
        """
        record = self.get_or_create(db, user_id)
        limit = record.limit_value or AI_TOKEN_DEFAULT_LIMIT
        if limit == -1:
            return True, record          # unlimited plan
        within_limit = (record.used or 0) < limit
        return within_limit, record

    def get_usage_info(self, db: Session, user_id: uuid.UUID, plan_limit: int | None = None) -> dict:
        """Return a dict with used / limit / remaining / percentage."""
        record = self.get_or_create(db, user_id)
        effective_limit = plan_limit if plan_limit is not None else (record.limit_value or AI_TOKEN_DEFAULT_LIMIT)
        used = record.used or 0
        if effective_limit == -1:
            return {
                "used": used,
                "limit": -1,
                "remaining": -1,
                "percentage": 0.0,
                "unlimited": True,
            }
        remaining = max(effective_limit - used, 0)
        percentage = round((used / effective_limit) * 100, 1) if effective_limit > 0 else 0.0
        return {
            "used": used,
            "limit": effective_limit,
            "remaining": remaining,
            "percentage": percentage,
            "unlimited": False,
        }

    def reset(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Reset the token counter to zero (for billing-cycle resets)."""
        record = self.get_or_create(db, user_id)
        record.used = 0
        db.commit()
        db.refresh(record)
        return record

    # ── Pay-Per-Feature helpers ───────────────────────────────────────────────

    def add_ppf_sections(self, db: Session, user_id: uuid.UUID, quantity: int) -> Usage:
        """Credit `quantity` PPF sections to the user (called after successful payment)."""
        record = self.get_or_create(db, user_id)
        record.ppf_purchased = (record.ppf_purchased or 0) + quantity
        db.commit()
        db.refresh(record)
        return record

    def consume_ppf_section(self, db: Session, user_id: uuid.UUID) -> Usage:
        """Deduct one PPF section credit (called when a section is generated)."""
        record = self.get_or_create(db, user_id)
        record.ppf_used = (record.ppf_used or 0) + 1
        db.commit()
        db.refresh(record)
        return record

    def get_ppf_balance(self, db: Session, user_id: uuid.UUID) -> int:
        """Return remaining PPF section credits (purchased minus consumed)."""
        record = self.get_or_create(db, user_id)
        return max((record.ppf_purchased or 0) - (record.ppf_used or 0), 0)


usage_repo = UsageRepository()
