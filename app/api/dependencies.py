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
from app.repositories.usage_repo import usage_repo, PPF_TOKENS_PER_SECTION
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Validate the JWT and return the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

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

    user.last_activity = now
    user_repo.save(db, db_obj=user)
    return user


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
    db: Session = Depends(get_db),
) -> User:
    """
    Gate-check AI token limits before forwarding to the AI service.

    Token counting strategy:
    - The bizifyAI service writes REAL token counts (from Groq usage.total_tokens)
      directly to the usages table after every LLM call.
    - This dependency only READS the current usage to enforce the plan limit.
    - GET requests (reading cached results) are always free.
    - POST/PUT/PATCH requests are checked against the limit before proceeding.
      If the user is already over their limit, the request is rejected here
      before any AI compute is consumed.
    """
    sub = subscription_repo.get_active_by_user(db, current_user.id)
    features: dict = {}
    if sub and sub.plan and sub.plan.features_json:
        features = sub.plan.features_json

    if features.get("ai_analysis") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your current plan does not include AI analysis features. Please upgrade your plan.",
        )

    # GET requests only read cached data — never count against quota
    if request.method == "GET":
        return current_user

    # PPF plan — skip subscription token check, only use credit balance
    if features.get("is_ppf"):
        ppf_balance = usage_repo.get_ppf_balance(db, current_user.id)
        if ppf_balance > 0:
            usage_repo.consume_ppf_section(db, current_user.id)
            usage_repo.add_tokens(db, current_user.id, PPF_TOKENS_PER_SECTION)
            return current_user
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No Pay-Per-Feature credits remaining. Buy more sections to continue.",
        )

    plan_limit: Optional[int] = features.get("ai_tokens")
    _, record = usage_repo.check_limit(db, current_user.id)
    active_limit = plan_limit if plan_limit is not None else (record.limit_value or 20_000)
    used = record.used or 0

    if active_limit == -1 or used < active_limit:
        return current_user

    # Subscription quota exhausted — fall back to PPF credits if any
    ppf_balance = usage_repo.get_ppf_balance(db, current_user.id)
    if ppf_balance > 0:
        usage_repo.consume_ppf_section(db, current_user.id)
        usage_repo.add_tokens(db, current_user.id, PPF_TOKENS_PER_SECTION)
        return current_user

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            f"AI token limit reached ({used:,}/{active_limit:,} tokens used). "
            "Upgrade your plan or buy Pay-Per-Feature credits to continue."
        ),
    )
