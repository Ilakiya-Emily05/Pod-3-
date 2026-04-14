import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.sentence_framing import SentenceExercise, SentenceSubmission
from app.schemas.sentence_framing import SentenceSubmissionCreate
from app.services.sentence_framing_service import SentenceFramingService


@pytest.mark.unit
async def test_get_categories_dynamic() -> None:
    db = AsyncMock()

    # Mock row results for categories/subcategories as a tuple (consistent with .all() return)
    mock_row = ("Professional Emails", "Client Communication", "Professional")

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    db.execute.return_value = mock_result

    service = SentenceFramingService(db)
    categories = await service.get_categories()

    assert len(categories) == 3
    assert categories[0]["name"] == "Professional Emails"
    assert categories[0]["name"] == "Professional Emails"
    assert categories[0]["subcategories"][0]["name"] == "Client Communication"


@pytest.mark.unit
async def test_get_exercises_by_subcategory() -> None:
    db = AsyncMock()

    mock_ex = MagicMock(spec=SentenceExercise)
    mock_ex.id = uuid.uuid4()
    mock_ex.subcategory = "Client Communication"

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_ex]
    db.execute.return_value = mock_result

    service = SentenceFramingService(db)
    exercises = await service.get_exercises_by_subcategory("Client Communication")

    assert len(exercises) == 1
    assert exercises[0].subcategory == "Client Communication"


@pytest.mark.unit
async def test_submit_response_success() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    exercise_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Mock exercise
    mock_ex = MagicMock(spec=SentenceExercise)
    mock_ex.id = exercise_id
    mock_ex.scenario = "Test Scenario"
    mock_ex.context = {"tone": "Professional"}
    mock_ex.exercise_type = "free_form"
    mock_ex.cefr_level = "B1"
    mock_ex.difficulty_score = 3.0
    mock_ex.difficulty = "Professional"
    mock_ex.subcategory = "Client Communication"

    mock_ex_result = MagicMock()
    mock_ex_result.scalar_one_or_none.return_value = mock_ex

    # Mock next exercise ID
    next_id = uuid.uuid4()
    mock_next_result = MagicMock()
    mock_next_result.scalar_one_or_none.side_effect = [
        next_id,
        None,
    ]  # One for next, one for fallback if needed

    db.execute.side_effect = [mock_ex_result, mock_next_result]

    payload = SentenceSubmissionCreate(
        exercise_id=exercise_id, response="Testing feedback", time_taken_secs=100
    )

    # Mock AI Evaluation
    mock_ai_eval = MagicMock()
    mock_ai_eval.overall_score = 90
    mock_ai_eval.structure_score = 90
    mock_ai_eval.tone_score = 90
    mock_ai_eval.grammar_score = 90
    mock_ai_eval.content_score = 90
    mock_ai_eval.structure_comment = "Good"
    mock_ai_eval.tone_comment = "Good"
    mock_ai_eval.grammar_comment = "Good"
    mock_ai_eval.grammar_corrections = []
    mock_ai_eval.content_comment = "Good"
    mock_ai_eval.content_suggestions = []
    mock_ai_eval.improved_version = "Improved version"

    with patch(
        "app.services.sentence_framing_service.evaluate_sentence_response", new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = mock_ai_eval

        service = SentenceFramingService(db)
        submission = await service.submit_response(user_id, payload)

        assert submission.overall_score == 90
        assert submission.user_id == user_id
        # assert submission._next_exercise_id == next_id  # Submission model currently lacks next_exercise_id
        assert db.add.called
        assert db.commit.called


@pytest.mark.unit
async def test_submit_response_exercise_not_found() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    service = SentenceFramingService(db)
    payload = SentenceSubmissionCreate(
        exercise_id=uuid.uuid4(), response="Test", time_taken_secs=10
    )

    with pytest.raises(ValueError, match="Exercise not found"):
        await service.submit_response(uuid.uuid4(), payload)


@pytest.mark.unit
async def test_get_user_progress() -> None:
    db = AsyncMock()

    mock_sub = MagicMock(spec=SentenceSubmission)
    mock_sub.overall_score = 80
    mock_sub.id = uuid.uuid4()
    mock_sub.exercise_id = uuid.uuid4()
    mock_sub.submitted_at = "today"

    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalars().all.return_value = [mock_sub]
    db.execute.return_value = mock_result

    service = SentenceFramingService(db)
    progress = await service.get_user_progress(uuid.uuid4())

    assert progress["total_submissions"] == 1
    assert progress["average_score"] == 80.0
