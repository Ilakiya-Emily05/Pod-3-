from __future__ import annotations

from dataclasses import dataclass

from app.models.assessment_status import CEFRLevel, is_valid_cefr_result_level

CEFR_LEVELS: list[CEFRLevel] = [
    CEFRLevel.A1,
    CEFRLevel.A2,
    CEFRLevel.B1,
    CEFRLevel.B2,
    CEFRLevel.C1,
    CEFRLevel.C2,
]

CEFR_DIFFICULTY_WEIGHT: dict[CEFRLevel, int] = {
    CEFRLevel.A1: 1,
    CEFRLevel.A2: 2,
    CEFRLevel.B1: 3,
    CEFRLevel.B2: 4,
    CEFRLevel.C1: 5,
    CEFRLevel.C2: 6,
}

CEFR_MASTERY_THRESHOLDS: dict[CEFRLevel, float] = {
    CEFRLevel.A1: 0.60,
    CEFRLevel.A2: 0.60,
    CEFRLevel.B1: 0.65,
    CEFRLevel.B2: 0.70,
    CEFRLevel.C1: 0.75,
    CEFRLevel.C2: 0.80,
}

BORDERLINE_PROMOTION_THRESHOLD = 0.50


@dataclass
class GradingResult:
    """Represent the CEFR grading output."""

    cefr_level: str
    ability_score: float
    accuracy_by_level: dict[str, float]


@dataclass
class LevelStats:
    """Represent per-level attempt counts."""

    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        """Return level accuracy ratio."""
        if self.total == 0:
            return 0.0
        return self.correct / self.total


class CEFRGradingService:
    """Grade attempts according to CEFR mastery and weighted ability."""

    def grade(self, attempts: list[dict]) -> GradingResult:
        """Grade attempts and return CEFR level plus weighted ability score."""
        level_stats = self._compute_level_stats(attempts)
        accuracy_by_level = {level.value: level_stats[level].accuracy for level in CEFR_LEVELS}

        base_level = self._compute_base_level(level_stats)
        ability_score = self._compute_ability_score(attempts)
        final_level = self._apply_borderline_promotion(base_level, accuracy_by_level)

        if not is_valid_cefr_result_level(final_level):
            msg = f"Invalid CEFR result level produced: {final_level}"
            raise ValueError(msg)

        return GradingResult(
            cefr_level=final_level,
            ability_score=round(ability_score, 4),
            accuracy_by_level=accuracy_by_level,
        )

    def _compute_level_stats(self, attempts: list[dict]) -> dict[CEFRLevel, LevelStats]:
        """Aggregate per-level correct and total counts."""
        stats: dict[CEFRLevel, LevelStats] = {level: LevelStats() for level in CEFR_LEVELS}

        for attempt in attempts:
            level = attempt["cefr_level"]
            if level not in stats:
                continue
            stats[level].total += 1
            if attempt["is_correct"]:
                stats[level].correct += 1

        return stats

    def _compute_base_level(self, level_stats: dict[CEFRLevel, LevelStats]) -> CEFRLevel:
        """Compute the highest mastered CEFR level using hierarchical thresholds."""
        base_level = CEFR_LEVELS[0]

        for level in CEFR_LEVELS:
            stats = level_stats[level]
            threshold = CEFR_MASTERY_THRESHOLDS[level]

            if stats.total == 0 or stats.accuracy < threshold:
                break
            base_level = level

        return base_level

    def _compute_ability_score(self, attempts: list[dict]) -> float:
        """Compute weighted ability score for all attempts.

        Uses question-provided difficulty_score when present; otherwise falls back
        to CEFR_DIFFICULTY_WEIGHT.
        """
        weighted_numerator = 0.0
        weighted_denominator = 0.0

        for attempt in attempts:
            level = attempt["cefr_level"]
            fallback_weight = CEFR_DIFFICULTY_WEIGHT[level]
            weight = float(attempt.get("difficulty_score") or fallback_weight)
            is_correct = bool(attempt["is_correct"])

            weighted_numerator += (1.0 if is_correct else 0.0) * weight
            weighted_denominator += weight

        if weighted_denominator == 0.0:
            return 0.0

        return weighted_numerator / weighted_denominator

    def _apply_borderline_promotion(
        self,
        base_level: CEFRLevel,
        accuracy_by_level: dict[str, float],
    ) -> str:
        """Apply promotion suffix when next-level accuracy is borderline strong."""
        index = CEFR_LEVELS.index(base_level)

        if index >= len(CEFR_LEVELS) - 1:
            return base_level.value

        next_level = CEFR_LEVELS[index + 1]
        if accuracy_by_level[next_level.value] >= BORDERLINE_PROMOTION_THRESHOLD:
            return f"{base_level.value}+"

        return base_level.value
