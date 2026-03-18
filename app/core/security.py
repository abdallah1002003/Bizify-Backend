from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token with an optional expiration time.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    
    to_encode.update({
        "exp": expire,
        "iat": issued_at
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm = settings.ALGORITHM)
    
    return encoded_jwt


def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password using the configured crypt context.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against its hashed version.
    """
    return pwd_context.verify(plain_password, hashed_password)