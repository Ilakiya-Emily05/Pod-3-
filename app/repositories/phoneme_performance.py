import uuid
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.pronunciation import PhonemePerformance


def upsert_phoneme(
    db: Session,
    user_id: uuid.UUID,
    phoneme: str,
    correct: bool,
    total_attempts: int = 1,
    correct_attempts: int | None = None,
) -> None:
    """
    Insert or update a PhonemePerformance row for (user_id, phoneme).

    On conflict (duplicate user_id + phoneme) the totals are accumulated
    and accuracy_pct is recomputed from the new totals.
    """
    if correct_attempts is None:
        correct_attempts = 1 if correct else 0

    now = datetime.now(UTC)

    stmt = insert(PhonemePerformance).values(
        id=uuid.uuid4(),
        user_id=user_id,
        phoneme=phoneme,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_pct=round(correct_attempts / total_attempts * 100, 2)
        if total_attempts > 0
        else 0.0,
        last_attempted_at=now,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "phoneme"],
        set_={
            "total_attempts": PhonemePerformance.total_attempts + total_attempts,
            "correct_attempts": PhonemePerformance.correct_attempts + correct_attempts,
            # Recompute accuracy from the new cumulative totals
            "accuracy_pct": (
                (PhonemePerformance.correct_attempts + correct_attempts)*100.0
                / (PhonemePerformance.total_attempts + total_attempts)
                
            ),
            "last_attempted_at": now,
        },
    )

    db.execute(stmt)
    # Caller is responsible for commit
