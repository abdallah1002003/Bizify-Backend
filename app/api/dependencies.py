from typing import Generator, Optional
from fastapi import Depends, HTTPException, status , Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.models.user import UserRole
from app.models.security_log import SecurityLog


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked (logged out)",
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub") 
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    now = datetime.utcnow()
    last_act = user.last_activity or now
    
    if now - last_act > timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to inactivity",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_activity = now
    db.commit()
        
    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    def __call__(self,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
        if current_user.role not in self.allowed_roles:
            new_log = SecurityLog(
                user_id=current_user.id,
                event_type="UNAUTHORIZED_ACCESS",
                details={
                    "path": str(request.url),
                    "method": request.method,
                    "required_roles": [role.value for role in self.allowed_roles],
                    "user_role": current_user.role.value
                },
                ip_address=request.client.host
            )
            db.add(new_log)
            db.commit()
               
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden"
            )
        return current_user