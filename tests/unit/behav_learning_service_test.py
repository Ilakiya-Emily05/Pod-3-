import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.behav_learning_hook import BehavioralLearningService


@pytest.fixture
def service():
    return BehavioralLearningService()


@pytest.mark.unit
def test_generate_recommendations_low_scores(service):
    # Test low scores triggering high priority recommendations
    profile = {
        "honesty_humility": 30.0,
        "conscientiousness": 45.0,
        "extraversion": 70.0,
    }

    recs = service.generate_recommendations(profile)

    # Honesty-Humility < 40 -> High priority
    # Conscientiousness < 60 -> Medium priority

    assert any(r.module == "business_ethics" and r.priority == "high" for r in recs)
    assert any(r.module == "time_management" and r.priority == "medium" for r in recs)

    # Check that reasons contain specific templates
    assert (
        "Identified as a primary development area" in recs[0].reason
        or "comparatively lower" in recs[0].reason
    )


@pytest.mark.unit
def test_generate_recommendations_high_emotionality(service):
    # Test high emotionality triggering stress management
    profile = {"emotionality": 90.0}

    recs = service.generate_recommendations(profile)

    assert any(r.module == "stress_management" and r.priority == "medium" for r in recs)
    assert "balance your very high" in recs[0].reason


@pytest.mark.unit
def test_generate_recommendations_comparative_low(service):
    # Test that even high scores trigger recommendations if they are the lowest in profile
    profile = {
        "honesty_humility": 100.0,
        "agreeableness": 90.0,
        "conscientiousness": 100.0,
    }

    recs = service.generate_recommendations(profile)

    # Agreeableness is the lowest (90), should trigger recommendations
    assert len(recs) > 0
    assert any(r.module == "conflict_resolution" for r in recs)
    assert "comparatively lower than your other strengths" in recs[0].reason


@pytest.mark.unit
async def test_process_assessment_completion(service):
    db = AsyncMock()
    db.add = MagicMock()
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_result = {
        "hexaco_scores": {"openness": 35.0},
        "strong_traits": [],
        "weak_traits": ["Openness"],
        "ai_analysis": {"summary": "Needs growth mindset."},
    }

    with patch(
        "app.services.behav_assessment_service.calculate_result", new_callable=AsyncMock
    ) as mock_calc:
        mock_calc.return_value = mock_result

        # Mock profile search (none found)
        mock_profile_result = MagicMock()
        mock_profile_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_profile_result

        response = await service.process_assessment_completion(db, user_id, session_id)

        assert response.user_id == user_id
        assert response.personality_summary == "Needs growth mindset."
        assert any(
            r.module == "growth_mindset" and r.priority == "high"
            for r in response.recommended_modules
        )
        assert db.add.called
        assert db.commit.called


@pytest.mark.unit
async def test_get_user_profile_not_found(service):
    db = AsyncMock()
    user_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="Behavioral profile not found"):
        await service.get_user_profile(db, user_id)
