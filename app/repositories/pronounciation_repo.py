from uuid import UUID

from sqlalchemy.orm import Session

from app.models.pronunciation_model import PronunciationResult


def save_pronunciation_result(db: Session, data: dict):
    """
    Save a new pronunciation result in the DB
    """
    result = PronunciationResult(
        user_id=data.get("user_id"),
        reference_text=data["reference_text"],
        transcript=data["transcript"],
        pronunciation_score=data["pronunciation_score"],
        total_mistakes=data.get("total_mistakes", 0),
        mistakes=data.get("mistakes"),
        improvement_tips=data.get("improvement_tips"),
        audio_path=data.get("audio_path"),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_user_results(db: Session, user_id: UUID):
    """
    Retrieve all pronunciation results for a user
    """
    return db.query(PronunciationResult).filter(PronunciationResult.user_id == user_id).all()


def get_latest_result(db: Session, user_id: UUID):
    """
    Retrieve the latest pronunciation result for a user
    """
    return (
        db.query(PronunciationResult)
        .filter(PronunciationResult.user_id == user_id)
        .order_by(PronunciationResult.created_at.desc())
        .first()
    )
