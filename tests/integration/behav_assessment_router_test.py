import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Patch before importing anything that might trigger engine creation
with patch("sqlalchemy.ext.asyncio.create_async_engine"), \
     patch("langchain_openai.AzureChatOpenAI"):
    from app.config.database import get_db
    from app.main import create_app
    from app.utils.auth import get_current_user_id

@pytest.fixture
async def client() -> AsyncClient:
    app = create_app()

    # Mock DB dependency
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock Auth dependency
    mock_uid = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: mock_uid

    # Mock service layer to avoid real AI/DB calls
    current_attempt_id = uuid.uuid4()
    with patch(
        "app.services.behav_assessment_service.get_dynamic_questions", new_callable=AsyncMock
    ) as mock_get_q, patch(
        "app.services.behav_assessment_service.calculate_result", new_callable=AsyncMock
    ) as mock_calc:
        # Create a mock question object
        mock_q = MagicMock()
        mock_q.id = 1
        mock_q.question_text = "Test question?"
        mock_q.trait_type = "Honesty-Humility"
        mock_q.options = [MagicMock(option_key="A", option_text="Text")]

        mock_get_q.return_value = {
            "attempt_id": current_attempt_id,
            "questions": [mock_q]
        }
        mock_calc.return_value = {
            "attempt_id": current_attempt_id,
            "status": "submitted",
            "hexaco_scores": {"honesty_humility": 80.0},
            "ai_analysis": {"summary": "Great"},
            "needs_adaptive_test": False,
            "weak_traits": [],
            "strong_traits": ["Honesty-Humility"],
            "comparative_low_traits": [],
            "recommendation": "None"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.mark.integration
async def test_fetch_questions(client: AsyncClient) -> None:
    """
    Test generating dynamic questions.
    """
    response = await client.get("/api/v1/behav-assessment/questions")
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
async def test_get_result(client: AsyncClient) -> None:
    """
    Test retrieving results with a valid attempt_id.
    """
    # Use a dummy UUID; the mock is set to return a successful result regardless of which UUID is passed
    attempt_id = uuid.uuid4()
    response = await client.get(f"/api/v1/behav-assessment/result?attempt_id={attempt_id}")
    assert response.status_code == 200
    data = response.json()
    assert "attempt_id" in data
    assert "hexaco_scores" in data
    assert "status" in data


@pytest.mark.integration
async def test_submit_answer_validation(client: AsyncClient) -> None:
    """
    Test submitting an answer with invalid schema (missing attempt_id).
    """
    response = await client.post("/api/v1/behav-assessment/answer", json={"question_id": 1, "option_key": "A"})
    assert response.status_code == 422
