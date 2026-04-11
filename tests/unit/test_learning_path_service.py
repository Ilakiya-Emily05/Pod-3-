from app.schemas.learning_path import AssessmentResults
from app.services.learning_path_service import (
    compute_learning_path,
    map_score_to_cefr,
    map_score_to_start_level,
)


def test_map_score_to_cefr_all_levels() -> None:
    assert map_score_to_cefr(10) == "A1"
    assert map_score_to_cefr(30) == "A2"
    assert map_score_to_cefr(50) == "B1"
    assert map_score_to_cefr(65) == "B2"
    assert map_score_to_cefr(80) == "C1"
    assert map_score_to_cefr(95) == "C2"


def test_map_score_to_start_level() -> None:
    assert map_score_to_start_level(40) == "basic"
    assert map_score_to_start_level(70) == "intermediate"
    assert map_score_to_start_level(92) == "advanced"


def test_compute_learning_path_placement_prep_prioritizes_goal_modules() -> None:
    assessment = AssessmentResults(
        grammar_score=65,
        reading_score=70,
        listening_score=55,
        speaking_score=60,
    )

    result = compute_learning_path(assessment, "placement_prep")

    assert result.cefr_level == "B2"
    assert "listening" in result.weak_areas
    assert result.recommended_path[0]["module"] == "listening"
    assert any(item["module"] == "mock_interview" for item in result.recommended_path)


def test_compute_learning_path_handles_strong_scores() -> None:
    assessment = AssessmentResults(
        grammar_score=90,
        reading_score=88,
        listening_score=92,
        speaking_score=94,
    )

    result = compute_learning_path(assessment, "promotion")

    assert result.cefr_level == "C2"
    assert result.weak_areas == []
    assert result.recommended_path[0]["module"] == "presentation_skills"
    assert result.recommended_path[0]["start_level"] == "advanced"
