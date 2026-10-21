"""
Cryptographic security utilities: Argon2 password hashing and JWT management.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any
import uuid

import argon2
import jwt

from app.core.errors import UnauthorizedError
from app.core.settings import get_settings
from app.modules.identity.enums import UserRole

# OWASP recommended default Argon2 parameters
_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days


def hash_password(password: str) -> str:
    """Hashes a password with Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2 hash in constant time."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.VerificationError):
        return False


def hash_token(token: str) -> str:
    """Returns SHA-256 digest of a refresh token to store in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: uuid.UUID,
    role: UserRole,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Creates a signed JWT access token containing user_id and role.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)
    return token, expires_at


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """
    Creates an opaque high-entropy refresh token and returns (raw_token, expires_at).
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    raw_token = f"gn_rt_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    return raw_token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a signed JWT access token.
    Raises UnauthorizedError if invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "role", "type"]},
        )
        if payload.get("type") != "access":
            raise UnauthorizedError(message="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(message="Session token has expired. Please log in again.")
    except jwt.PyJWTError:
        raise UnauthorizedError(message="Could not validate credentials.")
