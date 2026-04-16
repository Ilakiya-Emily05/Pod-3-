from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.auth import UserCreate, UserLogin
from app.services.auth_service import (
    get_current_user_profile,
    hash_password,
    login_user,
    register_user,
)
from app.utils.auth import CurrentUser


@pytest.mark.unit
async def test_register_user_creates_token() -> None:
    db = AsyncMock()
    db.scalar.return_value = None
    db.add = MagicMock()

    user_id = uuid4()

    async def set_user_id(obj: SimpleNamespace) -> None:
        obj.id = user_id

    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=set_user_id)

    with (
        patch("app.services.auth_service.create_access_token", return_value=("access_token", 1800)),
        patch("app.services.auth_service.create_refresh_token", return_value=("refresh_token", 604800)),
    ):
        response = await register_user(
            db,
            UserCreate(email="learner@example.com", password="Password123", name="Learner"),
        )

    assert response.user_id == user_id
    assert response.access_token == "access_token"
    assert response.refresh_token == "refresh_token"
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.unit
async def test_login_user_returns_token_pair() -> None:
    db = AsyncMock()
    db.commit = AsyncMock()

    user = SimpleNamespace(
        id=uuid4(),
        email="learner@example.com",
        name="Learner",
        password_hash=hash_password("Password123"),
        learning_goal="Speak fluently",
        learning_frequency="daily",
        streak_count=3,
        total_xp=120,
        last_active_date=None,
    )
    db.scalar.return_value = user

    with (
        patch("app.services.auth_service.create_access_token", return_value=("access", 1800)),
        patch("app.services.auth_service.create_refresh_token", return_value=("refresh", 604800)),
    ):
        response = await login_user(
            db,
            UserLogin(email="learner@example.com", password="Password123", remember_me=False),
        )

    assert response.access_token == "access"
    assert response.refresh_token == "refresh"
    assert response.user.email == "learner@example.com"
    assert response.user.total_xp == 120
    assert response.user.cefr_level is None  # CEFR level not fetched to avoid performance impact
    db.commit.assert_awaited_once()


@pytest.mark.unit
async def test_get_current_user_profile_returns_profile_fields() -> None:
    db = AsyncMock()
    user = SimpleNamespace(
        id=uuid4(),
        email="learner@example.com",
        name="Learner",
        learning_goal="Speak fluently",
        learning_frequency="daily",
        streak_count=5,
        total_xp=250,
    )
    db.scalar.return_value = user

    response = await get_current_user_profile(
        db,
        CurrentUser(user_id=user.id, email=user.email),
    )

    assert response.id == user.id
    assert response.email == "learner@example.com"
    assert response.streak_count == 5
    assert response.total_xp == 250
    assert response.cefr_level is None  # Not fetched to optimize /me endpoint
