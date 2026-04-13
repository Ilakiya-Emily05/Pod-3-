from unittest.mock import MagicMock

from app.services.leveling import (
    LEVEL_REQUIREMENTS,
    LEVEL_UP_SCORE_THRESHOLD,
    update_level_progress,
)


def make_profile(level="basic", exercises=0, avg_score=0.0, level_progress=None):
    profile = MagicMock()
    profile.current_level = level
    profile.exercises_completed = exercises
    profile.overall_score_avg = avg_score
    profile.level_progress = level_progress or {}
    return profile


class TestLevelProgress:
    def test_basic_level_progress_updates(self):
        profile = make_profile(level="basic", exercises=5, avg_score=50.0)
        update_level_progress(profile)
        assert profile.level_progress["current"] == "basic"
        assert profile.level_progress["exercises_at_level"] == 5
        assert profile.level_progress["required_for_next"] == LEVEL_REQUIREMENTS["basic"]

    def test_no_levelup_if_score_too_low(self):
        """User has enough exercises but score below threshold — should NOT level up."""
        profile = make_profile(
            level="basic",
            exercises=LEVEL_REQUIREMENTS["basic"],
            avg_score=LEVEL_UP_SCORE_THRESHOLD - 1,
        )
        update_level_progress(profile)
        assert profile.current_level == "basic"

    def test_no_levelup_if_exercises_insufficient(self):
        """User has high score but not enough exercises — should NOT level up."""
        profile = make_profile(
            level="basic",
            exercises=LEVEL_REQUIREMENTS["basic"] - 1,
            avg_score=LEVEL_UP_SCORE_THRESHOLD + 10,
        )
        update_level_progress(profile)
        assert profile.current_level == "basic"

    def test_levelup_basic_to_intermediate(self):
        """User meets both criteria — should level up to intermediate."""
        profile = make_profile(
            level="basic",
            exercises=LEVEL_REQUIREMENTS["basic"],
            avg_score=LEVEL_UP_SCORE_THRESHOLD + 5,
        )
        update_level_progress(profile)
        assert profile.current_level == "intermediate"
        assert profile.level_progress["current"] == "intermediate"
        assert profile.level_progress["exercises_at_level"] == 0

    def test_levelup_intermediate_to_advanced(self):
        profile = make_profile(
            level="intermediate",
            exercises=LEVEL_REQUIREMENTS["intermediate"],
            avg_score=LEVEL_UP_SCORE_THRESHOLD + 5,
        )
        update_level_progress(profile)
        assert profile.current_level == "advanced"

    def test_no_levelup_beyond_advanced(self):
        """Already at max level — should not promote further."""
        profile = make_profile(
            level="advanced",
            exercises=LEVEL_REQUIREMENTS["advanced"],
            avg_score=95.0,
        )
        update_level_progress(profile)
        assert profile.current_level == "advanced"

    def test_zero_exercises(self):
        profile = make_profile(level="basic", exercises=0, avg_score=0.0)
        update_level_progress(profile)
        assert profile.level_progress["exercises_at_level"] == 0
        assert profile.current_level == "basic"
