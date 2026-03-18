import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.security_log import SecurityLog
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to validate the JWT token and return the current authenticated user.
    Handles session timeout and token revocation checks.
    """
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers = {"WWW-Authenticate": "Bearer"},
    )
    
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    
    if blacklisted:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token has been revoked (logged out)",
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        issued_at_timestamp = payload.get("iat")
        
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "User account is deactivated",
        )

    if issued_at_timestamp:
        issued_at = datetime.fromtimestamp(issued_at_timestamp, tz = timezone.utc)
        
        if user.revoked_at:
            revoked_at = user.revoked_at
            if revoked_at.tzinfo is None:
                revoked_at = revoked_at.replace(tzinfo = timezone.utc)
            if issued_at < revoked_at:
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "Token has been revoked",
                )
        
        if user.last_password_change:
            last_change = user.last_password_change
            if last_change.tzinfo is None:
                last_change = last_change.replace(tzinfo = timezone.utc)
            if issued_at < last_change:
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "Session expired due to password change",
                )

    now = datetime.now(timezone.utc)
    last_act = user.last_activity
    if last_act and last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    else:
        last_act = last_act or now
    
    if now - last_act > timedelta(minutes = settings.SESSION_TIMEOUT_MINUTES):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Session expired due to inactivity",
            headers = {"WWW-Authenticate": "Bearer"},
        )

    user.last_activity = now
    db.commit()
    
    return user


class RoleChecker:
    """
    Dependency to check if the current user has the required roles.
    Logs unauthorized access attempts for security auditing.
    """

    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        Validates the user's role and logs unauthorized access attempts.
        """
        if current_user.role not in self.allowed_roles:
            new_log = SecurityLog(
                user_id = current_user.id,
                event_type = "UNAUTHORIZED_ACCESS",
                details = {
                    "path": str(request.url),
                    "method": request.method,
                    "required_roles": [role.value for role in self.allowed_roles],
                    "user_role": current_user.role.value
                },
                ip_address = request.client.host if request.client else "unknown"
            )
            db.add(new_log)
            db.commit()
               
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Forbidden"
            )
            
        return current_user