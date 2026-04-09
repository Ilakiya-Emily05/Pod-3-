import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pronunciation import UserPronunciationProfile

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/dashboard/{user_id}")
def get_dashboard(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Return the pronunciation progress for a specific user.

    Response format:
    {
        "pronunciation": {
            "total_levels": 5,
            "current_level": "intermediate",
            "completion_pct": 40.0,
            "avg_score": 68.0,
            "weak_phonemes": ["θ", "ð"],
            "strong_phonemes": ["s", "tʃ"],
            "time_spent_mins": 120
        }
    }
    """
    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User pronunciation profile not found")

    # Total levels (could be dynamic if needed)
    total_levels = 5

    # Compute completion percentage safely
    completion_pct = 0.0
    if hasattr(profile, "exercises_completed") and profile.exercises_completed:
        completion_pct = round(
            profile.exercises_completed / 50 * 100, 2
        )  # assuming 50 exercises = 100%

    # Extract weak phonemes (top 5)
    weak_phonemes = []
    if profile.weak_phonemes:
        if isinstance(profile.weak_phonemes[0], dict):
            weak_phonemes = [p.get("phoneme") for p in profile.weak_phonemes]
        else:
            weak_phonemes = list(profile.weak_phonemes)
    weak_phonemes = weak_phonemes[:5]

    # Extract strong phonemes (top 5)
    strong_phonemes = []
    if profile.strong_phonemes:
        if isinstance(profile.strong_phonemes[0], dict):
            strong_phonemes = [p.get("phoneme") for p in profile.strong_phonemes]
        else:
            strong_phonemes = list(profile.strong_phonemes)
    strong_phonemes = strong_phonemes[:5]

    # Time spent in minutes (round up if >0 but <1)
    time_spent_mins = (
        max(1, (profile.time_spent_total_secs or 0) // 60) if profile.time_spent_total_secs else 0
    )

    return {
        "pronunciation": {
            "total_levels": total_levels,
            "current_level": profile.current_level,
            "completion_pct": completion_pct,
            "avg_score": round(float(profile.overall_score_avg or 0), 2),
            "weak_phonemes": weak_phonemes,
            "strong_phonemes": strong_phonemes,
            "time_spent_mins": time_spent_mins,
        }
    }
