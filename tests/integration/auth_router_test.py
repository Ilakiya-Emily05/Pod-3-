from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

with (
    patch("sqlalchemy.ext.asyncio.create_async_engine"),
    patch("langchain_openai.AzureChatOpenAI", create=True),
):
    from app.config.database import get_db
    from app.controllers.routes.auth import router as auth_router
    from app.schemas.auth import AuthLoginResponse, AuthRegisterResponse, UserRead
    from app.utils.auth import CurrentUser, get_current_user


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=uuid4(), email="learner@example.com"
    )
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.integration
async def test_register_route(client: AsyncClient) -> None:
    user_id = uuid4()
    with patch(
        "app.controllers.routes.auth.register_user",
        new_callable=AsyncMock,
    ) as mock_register:
        mock_register.return_value = AuthRegisterResponse(user_id=user_id, token="token")
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "learner@example.com", "password": "Password123", "name": "Learner"},
        )

    assert response.status_code == 201
    assert response.json() == {"user_id": str(user_id), "token": "token"}


@pytest.mark.integration
async def test_login_route(client: AsyncClient) -> None:
    user = UserRead(
        id=uuid4(),
        email="learner@example.com",
        name="Learner",
        cefr_level="B1",
        learning_goal=None,
        learning_frequency=None,
        streak_count=0,
        total_xp=0,
    )
    with patch(
        "app.controllers.routes.auth.login_user",
        new_callable=AsyncMock,
    ) as mock_login:
        mock_login.return_value = AuthLoginResponse(
            access_token="access",
            refresh_token="refresh",
            user=user,
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "learner@example.com", "password": "Password123"},
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"
    assert response.json()["user"]["email"] == "learner@example.com"


@pytest.mark.integration
async def test_me_route(client: AsyncClient) -> None:
    user = UserRead(
        id=uuid4(),
        email="learner@example.com",
        name="Learner",
        cefr_level="B2",
        learning_goal="Speak fluently",
        learning_frequency="daily",
        streak_count=4,
        total_xp=200,
    )
    with patch(
        "app.controllers.routes.auth.get_current_user_profile",
        new_callable=AsyncMock,
    ) as mock_me:
        mock_me.return_value = user
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["cefr_level"] == "B2"
    assert response.json()["total_xp"] == 200
