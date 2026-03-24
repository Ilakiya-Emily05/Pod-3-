from typing import NamedTuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.settings import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class CurrentUser(NamedTuple):
    """Represents the current authenticated user extracted from the JWT token."""

    user_id: UUID
    email: str


def _decode_jwt_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict[str, object]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UUID:
    """Extract the user ID from the JWT token and validate it as a UUID.

    Args:
        credentials: The HTTP Bearer token credentials.

    Returns:
        The user ID as a UUID from the token's 'sub' claim.

    Raises:
        HTTPException: If credentials are missing, invalid, token is malformed,
                       or user_id is not a valid UUID.
    """
    payload = _decode_jwt_payload(credentials)
    user_id_str = payload.get("sub")
    if not isinstance(user_id_str, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user ID is not a valid UUID",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """Extract the current user's ID and email from the JWT token.

    Args:
        credentials: The HTTP Bearer token credentials.

    Returns:
        CurrentUser with validated user_id (UUID) and email from the token.

    Raises:
        HTTPException: If credentials are missing, invalid, token is malformed,
                       or user_id is not a valid UUID.
    """
    payload = _decode_jwt_payload(credentials)
    user_id_str = payload.get("sub")
    email = payload.get("email")

    if not isinstance(user_id_str, str) or not isinstance(email, str) or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID or email",
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user ID is not a valid UUID",
        )

    return CurrentUser(user_id=user_id, email=email)


async def get_current_admin_email(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    payload = _decode_jwt_payload(credentials)

    role = payload.get("role")
    email = payload.get("email")

    if role != "admin" or not isinstance(email, str) or not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return email
