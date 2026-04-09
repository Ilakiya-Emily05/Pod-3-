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

    progress.current_level = data.get("current_level")
    progress.overall_score_avg = data.get("avg_score")
    progress.weak_phonemes = data.get("weak_phonemes")

    # Convert minutes → seconds
    if data.get("time_spent_mins") is not None:
        progress.time_spent_total_secs = int(data["time_spent_mins"] * 60)

    # Store unsupported fields inside JSONB (level_progress)
    progress.level_progress = {
        "total_levels": data.get("total_levels"),
        "completion_pct": data.get("completion_pct"),
    }

    return progress
