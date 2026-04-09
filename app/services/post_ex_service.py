import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.pronunciation import PhonemePerformance, UserPronunciationProfile
from app.repositories.phoneme_performance import upsert_phoneme
from app.services.leveling import update_level_progress
import uuid

logger = logging.getLogger(__name__)


def update_phoneme_stats(db: Session, user_id: uuid.UUID, phoneme_results: list[dict]) -> None:
    """
    UPSERT phoneme performance rows for user_id.

    Each item in phoneme_results must contain:
        phoneme        (str)
        correct        (bool)
        total_attempts (int, optional, default 1)
        correct_attempts (int, optional)
    """
    for item in phoneme_results:
        phoneme = item.get("phoneme")
        if not phoneme:
            continue
        correct = bool(item.get("correct", False))
        total_attempts = int(item.get("total_attempts", 1))
        correct_attempts = int(item.get("correct_attempts", 1 if correct else 0))
        upsert_phoneme(
            db,
            user_id=user_id,
            phoneme=phoneme,
            correct=correct,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
        )
    # Caller is responsible for commit


def recompute_weak_strong_and_score(db: Session, profile: UserPronunciationProfile) -> None:
    """
    Recompute profile.weak_phonemes, strong_phonemes, and overall_score_avg
    from live PhonemePerformance rows.
    """
    phonemes = (
        db.query(PhonemePerformance).filter(PhonemePerformance.user_id == profile.user_id).all()
    )

    weak, strong, scores = [], [], []

    for p in phonemes:
        acc = float(p.accuracy_pct or 0)
        scores.append(acc)
        if acc < 50:
            weak.append({"phoneme": p.phoneme, "error_rate": round((100 - acc) / 100, 3)})
        elif acc >= 70:
            strong.append({"phoneme": p.phoneme, "accuracy": round(acc / 100, 3)})

    profile.weak_phonemes = weak
    profile.strong_phonemes = strong
    profile.overall_score_avg = round(sum(scores) / len(scores), 2) if scores else 0.0
    profile.last_practice_at = datetime.now(UTC)


def post_exercise_hook(
    db: Session,
    user_id: uuid.UUID,
    phoneme_results: list[dict],
    time_spent_secs: int,
    current_score: float,
) -> dict:
    """
    Run the complete post-exercise pipeline:
      1. Upsert phoneme performance rows.
      2. Increment exercise counters.
      3. Recompute aggregate stats.
      4. Evaluate level progression.
      5. Commit.

    Returns {"status": "success"} or {"status": "error", "message": ...}
    """
    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    try:
        update_phoneme_stats(db, user_id, phoneme_results)

        profile.exercises_completed = (profile.exercises_completed or 0) + 1
        profile.time_spent_total_secs = (profile.time_spent_total_secs or 0) + time_spent_secs

        recompute_weak_strong_and_score(db, profile)
        update_level_progress(profile)

        #db.commit()
        return {"status": "success"}
    except Exception as exc:
        db.rollback()
        logger.exception("post_exercise_hook failed for user_id=%s: %s", user_id, exc)
        return {"status": "error", "message": str(exc)}
