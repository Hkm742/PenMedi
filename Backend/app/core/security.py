import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
import bcrypt

# Ensure bcrypt compatibility with passlib in modern python
if not hasattr(bcrypt, "__about__"):
    class About:
        __version__ = getattr(bcrypt, "__version__", "5.0.0")
    bcrypt.__about__ = About()

# Ensure bcrypt truncate check doesn't crash on long passwords
_orig_hashpw = bcrypt.hashpw
def _safe_hashpw(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
bcrypt.hashpw = _safe_hashpw

from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Avoid passlib length issue for plain password > 72 bytes
        safe_password = plain_password[:72]
        return pwd_context.verify(safe_password, hashed_password)
    except Exception:
        # Fallback direct bcrypt verification
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8")[:72],
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    safe_password = password[:72]
    return pwd_context.hash(safe_password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    full_name: str,
    scopes: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "full_name": full_name,
        "scopes": scopes or [role],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
