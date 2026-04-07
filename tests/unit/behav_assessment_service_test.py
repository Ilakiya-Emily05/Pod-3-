import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import behav_assessment_service


@pytest.mark.unit
async def test_get_adaptive_questions_for_attempt():
    db = AsyncMock()
    db.add = MagicMock()
    attempt_id = uuid.uuid4()
    traits = ["Honesty-Humility"]

    with (
        patch(
            "app.services.behav_assessment_service.generate_adaptive_questions",
            new_callable=AsyncMock,
        ) as mock_gen,
        patch(
            "app.services.behav_assessment_service.save_questions_bulk", new_callable=AsyncMock
        ) as mock_save,
    ):
        mock_gen.return_value = [MagicMock()]
        mock_save.return_value = [MagicMock()]

        result = await behav_assessment_service.get_adaptive_questions_for_attempt(
            db, attempt_id, traits
        )

        assert len(result) == 1
        mock_gen.assert_called_once_with(traits)


@pytest.mark.unit
async def test_calculate_result_already_submitted():
    db = AsyncMock()
    attempt_id = uuid.uuid4()

    mock_attempt = MagicMock()
    mock_attempt.id = attempt_id
    mock_attempt.status = "submitted"
    mock_attempt.overall_report = {"summary": "Existing Report"}
    mock_attempt.scores = {"weak_traits": []}

    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar_one_or_none.return_value = mock_attempt
    db.execute.return_value = mock_result

    result = await behav_assessment_service.calculate_result(db, attempt_id)

    assert result["status"] == "submitted"
    assert result["ai_analysis"] == {"summary": "Existing Report"}


@pytest.mark.unit
@patch("app.services.behav_assessment_service.generate_assessment_questions")
@patch("app.services.behav_assessment_service.save_questions_bulk")
async def test_get_dynamic_questions_calls_ai(mock_save, mock_gen) -> None:
    db = AsyncMock()
    db.add = MagicMock()
    user_id = uuid.uuid4()

    mock_gen.return_value = []
    mock_save.return_value = []

    result = await behav_assessment_service.get_dynamic_questions(db, user_id)

    assert "attempt_id" in result
    assert "questions" in result
    mock_gen.assert_called_once()


@pytest.mark.unit
async def test_submit_answer_integration_logic() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    attempt_id = uuid.uuid4()
    question_id = 1
    option_key = "A"

    # Mock option
    mock_opt = MagicMock()
    mock_opt.id = 10

    # Mock attempt
    mock_attempt = MagicMock()
    mock_attempt.user_id = uuid.uuid4()
    mock_attempt.status = "in_progress"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [mock_opt, mock_attempt]
    db.execute.return_value = mock_result

    await behav_assessment_service.submit_answer(db, attempt_id, question_id, option_key)
    assert db.add.call_count >= 1


@pytest.mark.unit
async def test_submit_bulk_answers_integration_logic() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    attempt_id = uuid.uuid4()

    class MockAns:
        def __init__(self, q_id, opt_key):
            self.question_id = q_id
            self.option_key = opt_key

    answers = [MockAns(1, "A"), MockAns(2, "B")]

    # Mock attempt
    mock_attempt = MagicMock()
    mock_attempt.user_id = uuid.uuid4()
    mock_attempt.status = "in_progress"

    mock_attempt_result = MagicMock()
    mock_attempt_result.scalar_one_or_none.return_value = mock_attempt

    # Mock options
    mock_opt = MagicMock()
    mock_opt.id = 10
    mock_opt_result = MagicMock()
    mock_opt_result.scalar_one_or_none.return_value = mock_opt

    db.execute.side_effect = [mock_attempt_result, mock_opt_result, mock_opt_result]

    await behav_assessment_service.submit_bulk_answers(db, attempt_id, answers)
    assert db.commit.called


@pytest.mark.unit
async def test_calculate_result_integration_logic() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    attempt_id = uuid.uuid4()

    # Mock attempt with answers
    mock_attempt = MagicMock()
    mock_attempt.id = attempt_id
    mock_attempt.status = "in_progress"
    mock_attempt.answers = [MagicMock(option_id=1)]
    mock_attempt.overall_report = None
    mock_attempt.scores = {}

    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar_one_or_none.return_value = mock_attempt

    # Mock score result
    mock_score = MagicMock()
    mock_score.trait_name = "honesty_humility"
    mock_score.score_value = 5
    mock_score_result = MagicMock()
    mock_score_result.scalars().all.return_value = [mock_score]

    db.execute.side_effect = [mock_result, mock_score_result]

    with patch(
        "app.services.behav_assessment_service.generate_personality_report", new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = {"summary": "Test Report"}
        result = await behav_assessment_service.calculate_result(db, attempt_id)

        assert result["attempt_id"] == attempt_id
        assert "hexaco_scores" in result
        assert result["ai_analysis"] == {"summary": "Test Report"}


@pytest.mark.unit
async def test_submit_answer_invalid_option() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="Invalid option"):
        await behav_assessment_service.submit_answer(db, uuid.uuid4(), 1, "Z")


@pytest.mark.unit
async def test_submit_answer_invalid_attempt() -> None:
    db = AsyncMock()
    mock_opt = MagicMock()
    mock_opt.id = 10

    mock_opt_result = MagicMock()
    mock_opt_result.scalar_one_or_none.return_value = mock_opt

    mock_attempt_result = MagicMock()
    mock_attempt_result.scalar_one_or_none.return_value = None

    db.execute.side_effect = [mock_opt_result, mock_attempt_result]

    with pytest.raises(ValueError, match="Invalid or inactive attempt"):
        await behav_assessment_service.submit_answer(db, uuid.uuid4(), 1, "A")


@pytest.mark.unit
async def test_submit_bulk_answers_invalid_attempt() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="Invalid or inactive attempt"):
        await behav_assessment_service.submit_bulk_answers(db, uuid.uuid4(), [])


@pytest.mark.unit
async def test_calculate_result_invalid_attempt() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="Attempt not found"):
        await behav_assessment_service.calculate_result(db, uuid.uuid4())


@pytest.mark.unit
async def test_save_questions_bulk() -> None:
    db = AsyncMock()
    db.add = MagicMock()

    class MockOption:
        def __init__(self, text, score):
            self.option_text = text
            self.score = score

    class MockQuestionData:
        def __init__(self):
            self.question_text = "Test Question"
            self.trait = "honesty-humility"
            self.options = [MockOption("A", 1), MockOption("B", 2)]

    q_data = MockQuestionData()

    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalars().all.return_value = ["mock_question"]
    db.execute.return_value = mock_result

    result = await behav_assessment_service.save_questions_bulk(db, [q_data])

    assert result == ["mock_question"]
    assert db.add.call_count == 5  # 1 question + 2 options + 2 scores
