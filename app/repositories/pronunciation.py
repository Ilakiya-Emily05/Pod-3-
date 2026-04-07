import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.pronunciation import UserPronunciationProfile

logger = logging.getLogger(__name__)


def get_profile(db: Session, user_id: uuid.UUID) -> UserPronunciationProfile | None:
    return (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )


def get_or_create_profile(db: Session, user_id: uuid.UUID) -> UserPronunciationProfile:
    """Return existing profile or create a fresh one (flushed, not committed)."""
    profile = get_profile(db, user_id)
    if profile:
        return profile

    profile = UserPronunciationProfile(
        user_id=user_id,
        current_level="basic",
        overall_score_avg=0,
        exercises_completed=0,
        time_spent_total_secs=0,
        weak_phonemes=[],
        strong_phonemes=[],
        level_progress={},
        last_practice_at=datetime.now(UTC),
    )
    db.add(profile)
    db.flush()  # assign PK, satisfy FKs — caller must commit
    logger.debug("Created new pronunciation profile for user_id=%s", user_id)
    return profile
