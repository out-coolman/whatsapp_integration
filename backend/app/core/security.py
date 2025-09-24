"""
Security utilities for authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token authentication
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def verify_api_key(request: Request) -> bool:
    """Verify API key from headers."""
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        return False
    return api_key == settings.API_KEY


async def require_api_key(request: Request):
    """Dependency to require API key authentication."""
    if not verify_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional authentication for endpoints that can work with or without auth."""
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            return payload
    return None


def mask_pii(text: str) -> str:
    """
    Mask personally identifiable information in text.
    Replaces phone numbers, emails, and other PII with asterisks.
    """
    if not settings.MASK_PII_IN_LOGS:
        return text

    import re

    # Mask phone numbers (various formats)
    text = re.sub(r'\+?[\d\s\-\(\)]{8,}', '***PHONE***', text)

    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***', text)

    # Mask CPF (Brazilian tax ID)
    text = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '***CPF***', text)
    text = re.sub(r'\d{11}', '***CPF***', text)

    # Mask credit card numbers
    text = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '***CARD***', text)

    return text