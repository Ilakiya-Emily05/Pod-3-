import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Patch before importing anything that might trigger engine creation
with (
    patch("sqlalchemy.ext.asyncio.create_async_engine"),
    patch("langchain_openai.AzureChatOpenAI"),
    patch("openai.OpenAI"),
):
    from app.config.database import get_db
    from app.controllers.routes.analytics import router as analytics_router
    from app.services.analytics_service import AnalyticsService
    from app.utils.auth import get_current_user_id


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(analytics_router, prefix="/api/v1")

    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    return app


@pytest.fixture
async def client(app) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.integration
async def test_get_user_analytics_progress_success(client: AsyncClient, app) -> None:
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id

    mocked_payload = {
        "user_id": str(user_id),
        "overall_completion_pct": 65.5,
        "cefr_level": "B1",
        "modules": {
            "grammar": {
                "completion_pct": 80.0,
                "avg_score": 75.0,
                "weak_topics": ["prepositions"],
            },
            "pronunciation": {
                "completion_pct": 50.0,
                "current_level": "Intermediate",
            },
            "behavioral": {
                "completed": True,
                "hexaco_summary": {"honesty_humility": 78.0},
            },
        },
        "streak_days": 5,
        "last_activity": "2026-03-28T10:30:00Z",
    }

    with patch.object(
        AnalyticsService, "get_progress", new_callable=AsyncMock
    ) as mock_get_progress:
        mock_get_progress.return_value = mocked_payload
        response = await client.get(f"/api/v1/analytics/progress/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user_id)
    assert data["overall_completion_pct"] == 65.5
    assert data["modules"]["grammar"]["weak_topics"] == ["prepositions"]


@pytest.mark.integration
async def test_get_user_analytics_progress_forbidden_for_different_user(
    client: AsyncClient, app
) -> None:
    token_user_id = uuid.uuid4()
    requested_user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: token_user_id

    response = await client.get(f"/api/v1/analytics/progress/{requested_user_id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not authorized to access this user's analytics"


@pytest.mark.integration
async def test_get_user_analytics_heatmap_success(client: AsyncClient, app) -> None:
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id

    mocked_payload = {
        "topics": [
            {"name": "Tenses", "score": 85.0, "status": "strong"},
            {
                "name": "Pronunciation - Vowels",
                "score": 45.0,
                "status": "needs_work",
            },
        ]
    }

    with patch.object(AnalyticsService, "get_heatmap", new_callable=AsyncMock) as mock_get_heatmap:
        mock_get_heatmap.return_value = mocked_payload
        response = await client.get(f"/api/v1/analytics/heatmap/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 2
    assert data["topics"][0]["name"] == "Tenses"


@pytest.mark.integration
async def test_get_user_analytics_trends_success(client: AsyncClient, app) -> None:
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id

    mocked_payload = {
        "period": "30d",
        "data": [
            {"date": "2026-03-01T00:00:00Z", "avg_score": 72.5},
            {"date": "2026-03-02T00:00:00Z", "avg_score": 76.0},
        ],
    }

    with patch.object(AnalyticsService, "get_trends", new_callable=AsyncMock) as mock_get_trends:
        mock_get_trends.return_value = mocked_payload
        response = await client.get(f"/api/v1/analytics/trends/{user_id}?period=30d")

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "30d"
    assert len(data["data"]) == 2


@pytest.mark.integration
async def test_get_user_analytics_trends_invalid_period(client: AsyncClient, app) -> None:
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id

    with patch.object(AnalyticsService, "get_trends", new_callable=AsyncMock) as mock_get_trends:
        mock_get_trends.side_effect = ValueError("Unsupported period")
        response = await client.get(f"/api/v1/analytics/trends/{user_id}?period=7d")

    assert response.status_code == 422
    assert response.json()["detail"] == "Unsupported period"
