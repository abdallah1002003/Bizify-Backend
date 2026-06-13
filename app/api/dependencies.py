import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.repositories.admin_repo import security_repo
from app.repositories.auth_repo import auth_repo
from app.repositories.billing_repo import subscription_repo
from app.constants.credit_costs import get_route_info
from app.repositories.usage_repo import usage_repo, PPF_TOKENS_PER_SECTION, PRO_MONTHLY_CREDITS
from app.repositories.user_repo import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Provide a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """Validate the JWT and return the current authenticated user.

    Opens and closes its own DB session so the connection is returned to
    the pool immediately after auth completes — before long-running route
    handlers (e.g. AI forwarding, 30-120 s waits) even start executing.
    Using Depends(get_db) here would hold the connection open for the
    entire request lifetime, quickly exhausting the pool under load.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    db = SessionLocal()
    try:
        if auth_repo.is_token_blacklisted(db, token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked (logged out)",
            )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            issued_at_timestamp = payload.get("iat")
            if user_id is None:
                raise credentials_exception
        except JWTError as exc:
            raise credentials_exception from exc

        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError) as exc:
            raise credentials_exception from exc

        user = user_repo.get(db, user_uuid)
        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
            )

        if issued_at_timestamp:
            issued_at = datetime.fromtimestamp(issued_at_timestamp, tz=timezone.utc)

            if user.revoked_at:
                revoked_at = user.revoked_at
                if revoked_at.tzinfo is None:
                    revoked_at = revoked_at.replace(tzinfo=timezone.utc)
                if issued_at < revoked_at:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked",
                    )

            if user.last_password_change:
                last_change = user.last_password_change
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=timezone.utc)
                if issued_at < last_change:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session expired due to password change",
                    )

        now = datetime.now(timezone.utc)
        last_activity = user.last_activity
        if last_activity and last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        else:
            last_activity = last_activity or now

        if now - last_activity > timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Only write last_activity if it's stale by more than 5 minutes — avoids
        # a DB write + commit on every single request, which was the main source
        # of auth latency (300-750 ms per request at Supabase round-trip cost).
        if (now - last_activity) > timedelta(minutes=5):
            user.last_activity = now
            user_repo.save(db, db_obj=user)
            db.commit()
            db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()  # connection returned to pool BEFORE the route handler starts


class RoleChecker:
    """Authorize access based on the current user's role."""

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        """Validate the user's role and log unauthorized attempts."""
        if current_user.role not in self.allowed_roles:
            security_repo.log_event(
                db,
                user_id=current_user.id,
                event_type="UNAUTHORIZED_ACCESS",
                details={
                    "path": str(request.url),
                    "method": request.method,
                    "required_roles": [role.value for role in self.allowed_roles],
                    "user_role": current_user.role.value,
                },
                ip_address=request.client.host if request.client else "unknown",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )

        return current_user


get_current_admin_user = RoleChecker([UserRole.ADMIN])


def check_ai_usage(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Credit-based gate for every AI pipeline request.

    Strategy:
    - GET / DELETE / PATCH requests are always free (no credit cost).
    - POST/PUT requests look up the route in CREDIT_COSTS to find the cost.
    - Plan type is derived from the active subscription's features_json.
    - Plan gates block certain routes for Free users (marketing, roadmap, etc.).
    - Chat routes:
        - 'general': 20 turns/day counter for Free + PAYG; unlimited for subscribers.
        - 'section': blocked on Free; PAYG with ppf_purchased > 0; free for Pro/Premium.
    - Credit deduction:
        - Free/Subscribers: deduct from credits_used. If exhausted, fall back to PPF.
        - PAYG: consume 1 PPF section per generation/regen (not per chat).
    - Monthly renewal: Free users with credits_remaining == 0 receive 5 credits
      on the first of the next calendar month (checked on every request).
    """
    if request.method in ("GET", "HEAD", "OPTIONS", "DELETE", "PATCH"):
        return current_user

    db = SessionLocal()
    try:
        sub = subscription_repo.get_active_by_user(db, current_user.id)
        features: dict = sub.plan.features_json if (sub and sub.plan and sub.plan.features_json) else {}

        # Derive plan type
        is_ppf = bool(features.get("is_ppf"))
        plan_name = (sub.plan.name if sub and sub.plan else "Free").lower()
        if is_ppf:
            plan_type = "payg"
        elif plan_name in ("pro", "premium"):
            plan_type = plan_name
        else:
            plan_type = "free"

        # Lookup credit cost + gates for this route
        route = get_route_info(request.url.path, request.method)

        # ── Plan gate check ────────────────────────────────────────────────────
        if plan_type in route.plan_gates:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This feature is not available on your current plan. "
                    "Upgrade to Pro or purchase it as Pay-As-You-Go."
                ),
            )

        # ── Chat routes ────────────────────────────────────────────────────────
        if route.chat_type == "general":
            # Subscribers: unlimited chat — just allow
            if plan_type in ("pro", "premium"):
                return current_user
            # Free & PAYG: 20 turns/day
            allowed, turns = usage_repo.check_and_increment_chat(db, current_user.id)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Daily chat limit reached ({turns} / 20 turns). "
                        "Resets at midnight, or upgrade to Pro for unlimited chat."
                    ),
                )
            return current_user

        if route.chat_type == "section":
            # Pro/Premium: free unlimited section chat
            if plan_type in ("pro", "premium"):
                return current_user
            # PAYG: allowed if they have ever purchased at least one section
            if plan_type == "payg":
                record = usage_repo.get_or_create(db, current_user.id)
                if (record.ppf_purchased or 0) > 0:
                    return current_user
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Purchase a section to unlock section chat for that analysis.",
                )
            # Free: blocked (plan_gates already caught this above for routes that set it,
            # but section chat routes always gate Free — double-check here)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Section chat is available to Pro, Premium, and Pay-As-You-Go subscribers.",
            )

        # ── Free credit routes (0 credits, no chat type) ──────────────────────
        if route.credits == 0:
            return current_user

        # ── Credit-bearing generation / regeneration routes ───────────────────
        cost = route.credits

        if plan_type == "payg":
            # PAYG: consume 1 PPF section per feature run (pricing is handled at purchase)
            ppf_balance = usage_repo.get_ppf_balance(db, current_user.id)
            if ppf_balance > 0:
                usage_repo.consume_ppf_section(db, current_user.id)
                return current_user
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="No Pay-As-You-Go credits remaining. Purchase a feature run to continue.",
            )

        # Subscription path (Free, Pro, Premium). Chat is already free/unlimited
        # for Pro & Premium (handled above); here we only gate credit-bearing
        # generation/regeneration routes against the plan's monthly credit pool.
        # Premium is NOT unlimited — it has a 150-credit/month allowance.
        if plan_type == "free":
            usage_repo.maybe_grant_free_monthly_credits(db, current_user.id)
        elif plan_type == "pro":
            usage_repo.maybe_grant_pro_monthly_credits(db, current_user.id)
            usage_repo.reconcile_subscriber_credit_limit(db, current_user.id, plan_type)
        elif plan_type == "premium":
            usage_repo.maybe_grant_premium_monthly_credits(db, current_user.id)
            usage_repo.reconcile_subscriber_credit_limit(db, current_user.id, plan_type)

        remaining = usage_repo.get_credits_remaining(db, current_user.id)
        if remaining >= cost:
            usage_repo.deduct_credits(db, current_user.id, cost)
            return current_user

        # Credits exhausted — fall back to PAYG if user has PPF credits
        ppf_balance = usage_repo.get_ppf_balance(db, current_user.id)
        if ppf_balance > 0:
            usage_repo.consume_ppf_section(db, current_user.id)
            return current_user

        # Determine the right error message by plan
        if plan_type == "free":
            remaining_cr = usage_repo.get_credits_remaining(db, current_user.id)
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Not enough credits (need {cost}, have {remaining_cr}). "
                    "Upgrade to Pro for 90 credits/month, or buy this feature as Pay-As-You-Go."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Monthly credit limit reached (need {cost} credits). "
                "Buy more as Pay-As-You-Go or wait for your next billing cycle."
            ),
        )
    finally:
        db.close()
