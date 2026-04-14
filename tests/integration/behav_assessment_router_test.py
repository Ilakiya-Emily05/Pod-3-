import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Mock problematic modules that are out of scope but break app startup during collection
mock_router = MagicMock()
sys.modules["app.controllers.routes.interview"] = MagicMock()
sys.modules["app.controllers.routes.interview"].router = mock_router
sys.modules["app.controllers.routes.practice"] = MagicMock()
sys.modules["app.controllers.routes.practice"].router = mock_router
sys.modules["app.services.interview_service"] = MagicMock()
sys.modules["app.routes.audio_route"] = MagicMock()
sys.modules["app.routes.audio_route"].router = mock_router
sys.modules["app.controllers.routes.admin"] = MagicMock()
sys.modules["app.controllers.routes.admin"].router = mock_router

import pytest
from httpx import ASGITransport, AsyncClient

# Patch before importing anything that might trigger engine creation
with (
    patch("sqlalchemy.ext.asyncio.create_async_engine"),
    patch("langchain_openai.AzureChatOpenAI", create=True),
):
    from app.config.database import get_db
    from app.main import create_app
    from app.utils.auth import get_current_user_id


from collections.abc import AsyncGenerator


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    # Mock DB dependency
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock Auth dependency
    mock_uid = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: mock_uid

    # Mock service layer to avoid real AI/DB calls
    current_attempt_id = uuid.uuid4()
    with (
        patch(
            "app.services.behav_assessment_service.get_dynamic_questions", new_callable=AsyncMock
        ) as mock_get_q,
        patch(
            "app.services.behav_assessment_service.calculate_result", new_callable=AsyncMock
        ) as mock_calc,
    ):
        # Create a mock question object
        mock_q = MagicMock()
        mock_q.id = uuid.uuid4()
        mock_q.question_text = "Test question?"
        mock_q.trait_type = "Honesty-Humility"
        mock_q.options = [MagicMock(option_key="A", option_text="Text")]

        mock_get_q.return_value = {"attempt_id": current_attempt_id, "questions": [mock_q]}
        mock_calc.return_value = {
            "attempt_id": current_attempt_id,
            "status": "submitted",
            "hexaco_scores": {"honesty_humility": 80.0},
            "ai_analysis": {"summary": "Great"},
            "needs_adaptive_test": False,
            "weak_traits": [],
            "strong_traits": ["Honesty-Humility"],
            "comparative_low_traits": [],
            "recommendation": "None",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.mark.integration
async def test_fetch_questions(client: AsyncClient) -> None:
    """
    Test generating dynamic questions.
    """
    response = await client.get("/api/v1/behavioral/questions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "attempt_id" in data
    assert "questions" in data
    assert isinstance(data["questions"], list)
    if len(data["questions"]) > 0:
        assert "question_text" in data["questions"][0]
        assert "options" in data["questions"][0]


@pytest.mark.integration
async def test_submit_questions_valid(client: AsyncClient) -> None:
    """
    Test submitting multiple answers (bulk) to the consolidated /answer endpoint.
    """
    attempt_id = uuid.uuid4()
    payload = {
        "attempt_id": str(attempt_id),
        "answers": [
            {"attempt_id": str(attempt_id), "question_id": str(uuid.uuid4()), "option_key": "A"},
            {"attempt_id": str(attempt_id), "question_id": str(uuid.uuid4()), "option_key": "B"},
        ],
    }
    with patch(
        "app.services.behav_assessment_service.submit_bulk_answers", new_callable=AsyncMock
    ) as mock_submit:
        response = await client.post("/api/v1/behavioral/answer", json=payload)
        assert response.status_code == 200
        assert "recorded" in response.json()["message"]
        mock_submit.assert_called_once()


@pytest.mark.integration
async def test_submit_answer_validation(client: AsyncClient) -> None:
    """
    Test submitting an answer with invalid schema (passing a single object instead of bulk list).
    """
    response = await client.post(
        "/api/v1/behavioral/answer", json={"question_id": str(uuid.uuid4()), "option_key": "A"}
    )
    assert response.status_code == 422


@pytest.mark.integration
async def test_complete_assessment(client: AsyncClient) -> None:
    """
    Test the assessment completion endpoint.
    """
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    payload = {"user_id": str(user_id), "session_id": str(session_id)}

    with patch(
        "app.services.behav_learning_hook.behav_learning_service.process_assessment_completion",
        new_callable=AsyncMock,
    ) as mock_complete:
        from app.schemas.behav_assessment_schemas import (
            BehavioralCompleteResponse,
            ModuleRecommendation,
        )

        mock_complete.return_value = BehavioralCompleteResponse(
            user_id=user_id,
            hexaco_profile={"openness": 88.0},
            personality_summary="Creative",
            recommended_modules=[
                ModuleRecommendation(
                    module="creative_thinking", reason="High openness", priority="medium", difficulty="intermediate"
                )
            ],
            learning_path_updated=True,
        )

        response = await client.post("/api/v1/behavioral/complete", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert "hexaco_profile" in data


@pytest.mark.integration
async def test_get_profile(client: AsyncClient) -> None:
    """
    Test retrieving the behavioral profile.
    """
    user_id = uuid.uuid4()
    with patch(
        "app.services.behav_learning_hook.behav_learning_service.get_user_profile",
        new_callable=AsyncMock,
    ) as mock_profile:
        from app.schemas.behav_assessment_schemas import BehavioralProfileResponse, TraitScore

        mock_profile.return_value = BehavioralProfileResponse(
            user_id=user_id,
            completed_at=datetime.now(),
            hexaco_scores={"openness": TraitScore(score=88.0, level="high")},
            strengths=["Creativity"],
            development_areas=[],
            ai_personality_report="You are highly creative.",
            needs_adaptive_test=True,
        )

        response = await client.get(f"/api/v1/behavioral/profile/{user_id}")
        assert response.status_code == 200
        assert response.json()["user_id"] == str(user_id)


@pytest.mark.integration
async def test_get_recommendations(client: AsyncClient) -> None:
    """
    Test retrieving behavioral recommendations.
    """
    user_id = uuid.uuid4()
    with patch(
        "app.services.behav_learning_hook.behav_learning_service.get_recommendations",
        new_callable=AsyncMock,
    ) as mock_recs:
        from app.schemas.behav_assessment_schemas import ModuleRecommendation

        mock_recs.return_value = [
            ModuleRecommendation(
                module="creative_thinking", reason="Strategic necessity", priority="medium", difficulty="intermediate"
            )
        ]

        response = await client.get(f"/api/v1/behavioral/recommendations/{user_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["module"] == "creative_thinking"
