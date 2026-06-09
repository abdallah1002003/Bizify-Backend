import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.usage import Usage

AI_TOKEN_RESOURCE_TYPE = "ai_tokens"

# Default token budget kept for legacy analytics; not used for gating anymore.
AI_TOKEN_DEFAULT_LIMIT = 20_000

# Tokens reserved per PPF section purchase (kept for legacy compatibility)
PPF_TOKENS_PER_SECTION = 3_000

# Free plan: 15 starter credits on sign-up, then 5 credits/month when balance hits 0
FREE_STARTER_CREDITS = 15
FREE_MONTHLY_RENEWAL = 5

# Pro plan: 90 credits/month
PRO_MONTHLY_CREDITS = 90

# Premium plan: treated as unlimited — set_plan_credits uses this sentinel;
# check_ai_usage short-circuits before the credit check for premium users.
PREMIUM_MONTHLY_CREDITS = 9999

# Daily general-chat turn limit for Free and PAYG users
CHAT_DAILY_LIMIT = 20


class UsageRepository:
    """Data-access helpers for `Usage` records."""

    # ── Internal helpers ──────────────────────────────────────────────────────

    def get_or_create(self, db: Session, user_id: uuid.UUID) -> Usage:
        record = (
            db.query(Usage)
            .filter(Usage.user_id == user_id, Usage.resource_type == AI_TOKEN_RESOURCE_TYPE)
            .first()
        )
        if record is None:
            record = Usage(
                user_id=user_id,
                resource_type=AI_TOKEN_RESOURCE_TYPE,
                used=0,
                limit_value=AI_TOKEN_DEFAULT_LIMIT,
                credits_used=0,
                credits_limit=FREE_STARTER_CREDITS,
                period_start=date.today(),
                chat_turns_today=0,
                chat_turns_date=date.today(),
                ppf_purchased=0,
                ppf_used=0,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record

    # ── Legacy token helpers (kept for analytics) ─────────────────────────────

    def add_tokens(self, db: Session, user_id: uuid.UUID, tokens: int) -> Usage:
        record = self.get_or_create(db, user_id)
        record.used = (record.used or 0) + max(tokens, 0)
        db.commit()
        db.refresh(record)
        return record

    def check_limit(self, db: Session, user_id: uuid.UUID) -> tuple[bool, Usage]:
        record = self.get_or_create(db, user_id)
        limit = record.limit_value or AI_TOKEN_DEFAULT_LIMIT
        if limit == -1:
            return True, record
        within_limit = (record.used or 0) < limit
        return within_limit, record

    def get_usage_info(self, db: Session, user_id: uuid.UUID, plan_limit: Optional[int] = None) -> dict:
        record = self.get_or_create(db, user_id)
        effective_limit = plan_limit if plan_limit is not None else (record.limit_value or AI_TOKEN_DEFAULT_LIMIT)
        used = record.used or 0
        if effective_limit == -1:
            return {"used": used, "limit": -1, "remaining": -1, "percentage": 0.0, "unlimited": True}
        remaining = max(effective_limit - used, 0)
        percentage = round((used / effective_limit) * 100, 1) if effective_limit > 0 else 0.0
        return {"used": used, "limit": effective_limit, "remaining": remaining, "percentage": percentage, "unlimited": False}

    def reset(self, db: Session, user_id: uuid.UUID) -> Usage:
        record = self.get_or_create(db, user_id)
        record.used = 0
        db.commit()
        db.refresh(record)
        return record

    # ── Credit system ─────────────────────────────────────────────────────────

    def get_credits_remaining(self, db: Session, user_id: uuid.UUID) -> int:
        record = self.get_or_create(db, user_id)
        limit = record.credits_limit or 0
        used = record.credits_used or 0
        return max(limit - used, 0)

    def deduct_credits(self, db: Session, user_id: uuid.UUID, amount: int) -> Usage:
        """Deduct `amount` credits. Caller must verify balance before calling."""
        record = self.get_or_create(db, user_id)
        record.credits_used = (record.credits_used or 0) + max(amount, 0)
        db.commit()
        db.refresh(record)
        return record

    def add_credits(self, db: Session, user_id: uuid.UUID, amount: int) -> Usage:
        """Add credits to the limit (e.g., on plan upgrade or monthly renewal)."""
        record = self.get_or_create(db, user_id)
        record.credits_limit = (record.credits_limit or 0) + max(amount, 0)
        db.commit()
        db.refresh(record)
        return record

    def set_plan_credits(self, db: Session, user_id: uuid.UUID, credits_limit: int) -> Usage:
        """
        Reset the billing period with a new credit allowance.
        Called when a subscription activates or renews.
        """
        record = self.get_or_create(db, user_id)
        record.credits_used = 0
        record.credits_limit = credits_limit
        record.period_start = date.today()
        db.commit()
        db.refresh(record)
        return record

    def maybe_grant_pro_monthly_credits(self, db: Session, user_id: uuid.UUID) -> bool:
        """
        Reset a Pro user's credit balance to PRO_MONTHLY_CREDITS on the first
        request of a new calendar month. Returns True if credits were renewed.
        """
        record = self.get_or_create(db, user_id)
        today = date.today()
        period_start = record.period_start or today
        if today.year > period_start.year or today.month > period_start.month:
            record.credits_used = 0
            record.credits_limit = PRO_MONTHLY_CREDITS
            record.period_start = date(today.year, today.month, 1)
            db.commit()
            db.refresh(record)
            return True
        return False

    def maybe_grant_free_monthly_credits(self, db: Session, user_id: uuid.UUID) -> bool:
        """
        Grant FREE_MONTHLY_RENEWAL credits to a Free user if:
          - Their credit balance has hit 0
          - At least one calendar month has passed since period_start

        Returns True if credits were granted.
        """
        record = self.get_or_create(db, user_id)
        today = date.today()
        remaining = max((record.credits_limit or 0) - (record.credits_used or 0), 0)
        if remaining > 0:
            return False

        period_start = record.period_start or today
        # A new month has started relative to the period_start
        if today.year > period_start.year or today.month > period_start.month:
            record.credits_used = 0
            record.credits_limit = FREE_MONTHLY_RENEWAL
            record.period_start = date(today.year, today.month, 1)
            db.commit()
            db.refresh(record)
            return True
        return False

    def get_credit_info(self, db: Session, user_id: uuid.UUID) -> dict:
        record = self.get_or_create(db, user_id)
        limit = record.credits_limit or 0
        used = record.credits_used or 0
        remaining = max(limit - used, 0)
        return {
            "credits_used": used,
            "credits_limit": limit,
            "credits_remaining": remaining,
            "period_start": record.period_start.isoformat() if record.period_start else None,
        }

    # ── Chat daily limit ──────────────────────────────────────────────────────

    def check_and_increment_chat(self, db: Session, user_id: uuid.UUID) -> tuple[bool, int]:
        """
        Check if the user is within the daily chat limit, then increment.
        Returns (allowed, turns_used_after_increment).
        Resets the counter automatically when the date changes.
        """
        record = self.get_or_create(db, user_id)
        today = date.today()

        if record.chat_turns_date != today:
            record.chat_turns_today = 0
            record.chat_turns_date = today

        current = record.chat_turns_today or 0
        if current >= CHAT_DAILY_LIMIT:
            db.commit()
            return False, current

        record.chat_turns_today = current + 1
        db.commit()
        return True, current + 1

    def get_chat_turns_remaining(self, db: Session, user_id: uuid.UUID) -> int:
        record = self.get_or_create(db, user_id)
        today = date.today()
        if record.chat_turns_date != today:
            return CHAT_DAILY_LIMIT
        return max(CHAT_DAILY_LIMIT - (record.chat_turns_today or 0), 0)

    # ── Pay-Per-Feature helpers ───────────────────────────────────────────────

    def add_ppf_sections(self, db: Session, user_id: uuid.UUID, quantity: int) -> Usage:
        record = self.get_or_create(db, user_id)
        record.ppf_purchased = (record.ppf_purchased or 0) + quantity
        db.commit()
        db.refresh(record)
        return record

    def consume_ppf_section(self, db: Session, user_id: uuid.UUID) -> Usage:
        record = self.get_or_create(db, user_id)
        record.ppf_used = (record.ppf_used or 0) + 1
        db.commit()
        db.refresh(record)
        return record

    def get_ppf_balance(self, db: Session, user_id: uuid.UUID) -> int:
        record = self.get_or_create(db, user_id)
        return max((record.ppf_purchased or 0) - (record.ppf_used or 0), 0)


usage_repo = UsageRepository()
