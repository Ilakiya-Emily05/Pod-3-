import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Patch before importing anything that might trigger engine creation
with patch("sqlalchemy.ext.asyncio.create_async_engine"), patch("langchain_openai.AzureChatOpenAI"):
    from app.config.database import get_db
    from app.main import create_app
    from app.services.analytics_service import AnalyticsService
    from app.utils.auth import get_current_user_id


@pytest.fixture
def app():
    app = create_app()

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

    with patch.object(AnalyticsService, "get_progress", new_callable=AsyncMock) as mock_get_progress:
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
