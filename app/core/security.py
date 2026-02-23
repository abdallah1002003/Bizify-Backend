from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, cast
from uuid import uuid4
from jose import jwt
from passlib.context import CryptContext
from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid4()), "type": "access"}
    encoded_jwt = cast(str, jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM))
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default to 7 days for refresh token
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid4()), "type": "refresh"}
    return cast(str, jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM))

def create_password_reset_token(email: str) -> str:
    """Create a short-lived token for password reset (15 mins) with JTI."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "password_reset", "jti": str(uuid4())}
    return cast(str, jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM))

def verify_password_reset_token(token: str) -> Optional[dict]:
    """Verify reset token and return full payload if valid."""
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded_token.get("type") != "password_reset":
            return None
        return decoded_token
    except jwt.JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, hashed_password))

def get_password_hash(password: str) -> str:
    return cast(str, pwd_context.hash(password))
