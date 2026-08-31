"""Authentication, password hashing, JWT, and role-based access control."""

from __future__ import annotations

import enum
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

ALGORITHM = "HS256"

# bcrypt operates on at most 72 bytes; longer inputs are truncated consistently
# for both hashing and verification.
_BCRYPT_MAX_BYTES = 72

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/token")


class Role(enum.StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


# Privilege ordering — higher index grants everything below it.
_ROLE_RANK = {Role.VIEWER: 0, Role.ENGINEER: 1, Role.MANAGER: 2, Role.ADMIN: 3}


class TokenData(BaseModel):
    sub: str
    role: Role
    org_id: str | None = None
    is_superuser: bool = False


def hash_password(plain: str) -> str:
    pw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(pw, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: TokenData, expires_minutes: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {
        "sub": data.sub,
        "role": data.role.value,
        "org_id": data.org_id,
        "is_superuser": data.is_superuser,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        role = payload.get("role")
        if subject is None or role is None:
            raise credentials_error
        return TokenData(
            sub=subject,
            role=Role(role),
            org_id=payload.get("org_id"),
            is_superuser=bool(payload.get("is_superuser", False)),
        )
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return decode_token(token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def require_role(minimum: Role):
    """Dependency factory enforcing a minimum role in the privilege hierarchy."""

    def _guard(user: CurrentUser) -> TokenData:
        if _ROLE_RANK[user.role] < _ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum.value}' role or higher",
            )
        return user

    return _guard


def require_superuser(user: CurrentUser) -> TokenData:
    """Dependency that allows only platform superusers (admin panel)."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required",
        )
    return user
