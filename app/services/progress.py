import uuid

from sqlalchemy.orm import Session

from app.repositories.progress import (
    get_phoneme_rows,
    upsert_progress,
)

TOTAL_SYSTEM_PHONEMES = 40
WEAK_THRESHOLD = 60


def compute_progress(rows):
    if not rows:
        return {
            "total_levels": 5,
            "current_level": "beginner",
            "completion_pct": 0.0,
            "avg_score": 0.0,
            "weak_phonemes": [],
            "time_spent_mins": 0,
        }

    total = len(rows)

    avg_score = sum(r.accuracy_pct for r in rows) / total

    weak_phonemes = [r.phoneme for r in rows if r.accuracy_pct < WEAK_THRESHOLD]

    completion_pct = (total / TOTAL_SYSTEM_PHONEMES) * 100

    if avg_score < 50:
        level = "beginner"
    elif avg_score < 75:
        level = "intermediate"
    else:
        level = "advanced"

    return {
        "total_levels": 5,
        "current_level": level,
        "completion_pct": round(completion_pct, 2),
        "avg_score": round(avg_score, 2),
        "weak_phonemes": weak_phonemes,
        "time_spent_mins": 120,  # replace later with real tracking
    }


def update_user_progress(db: Session, user_id: uuid.UUID):
    rows = get_phoneme_rows(db, user_id)

    data = compute_progress(rows)

    progress = upsert_progress(db, user_id, data)

    db.commit()
    db.refresh(progress)

    return progress
