from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.config.settings import get_settings
from app.utils.auth import get_current_user


@pytest.mark.unit
async def test_get_current_user_accepts_access_token() -> None:
    settings = get_settings()
    user_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": "learner@example.com",
        "role": "student",
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    current_user = await get_current_user(credentials)

    assert current_user.user_id == user_id
    assert current_user.email == "learner@example.com"


@pytest.mark.unit
async def test_get_current_user_rejects_refresh_token() -> None:
    settings = get_settings()
    user_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": "learner@example.com",
        "role": "student",
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token type: expected 'access'"
