import uuid

from sqlalchemy.orm import Session

from app.models.pronunciation import (
    PhonemePerformance,
    UserPronunciationProfile,
)


def get_phoneme_rows(db: Session, user_id: uuid.UUID):
    return db.query(PhonemePerformance).filter(PhonemePerformance.user_id == user_id).all()


def get_progress(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )


def upsert_progress(db: Session, user_id: uuid.UUID, data: dict):
    progress = get_progress(db, user_id)

    if not progress:
        progress = UserPronunciationProfile(user_id=user_id)
        db.add(progress)

    progress.total_levels = data["total_levels"]
    progress.current_level = data["current_level"]
    progress.completion_pct = data["completion_pct"]
    progress.avg_score = data["avg_score"]
    progress.weak_phonemes = data["weak_phonemes"]
    progress.time_spent_mins = data["time_spent_mins"]

    return progress
