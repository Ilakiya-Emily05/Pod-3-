from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.interview_system import InterviewSession, UserResponse
from app.services.interview_service import (
    get_user_sessions,
    get_session_result,
    get_improvement_history,
)

router = APIRouter(prefix="/api/v1/interview", tags=["Interview History"])


# ── 1. HISTORY API ────────────────────────────────────────────────
@router.get("/history/{user_id}")
async def history(
    user_id: str,
    page: int = Query(1),
    limit: int = Query(10),
    interview_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    data = await get_user_sessions(db, user_id, page, limit, interview_type)
    sessions = data["sessions"]

    # Date filtering
    if date_from:
        sessions = [s for s in sessions if s["date"] >= date_from]
    if date_to:
        sessions = [s for s in sessions if s["date"] <= date_to]

    # Summary block
    scores = [s["overall_score"] for s in sessions if s["overall_score"]]
    summary = {
        "total_interviews": data["total"],
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "total_time_mins": sum([s["duration_mins"] or 0 for s in sessions]),
    }

    return {
        **data,
        "sessions": sessions,
        "summary": summary,
    }


# ── 2. REPLAY API ─────────────────────────────────────────────────
@router.get("/session/{session_id}/replay")
async def replay(session_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await get_session_result(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── 3. PROGRESS API ───────────────────────────────────────────────
@router.get("/progress/{user_id}")
async def progress(user_id: str, db: AsyncSession = Depends(get_db)):
    return await get_improvement_history(db, user_id)


# ── 4. SOFT DELETE ────────────────────────────────────────────────
@router.delete("/session/{session_id}")
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        update(InterviewSession)
        .where(InterviewSession.id == session_id)
        .values(deleted_at=datetime.utcnow())
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "Session deleted successfully"}


# ── 5. AUDIO FETCH ────────────────────────────────────────────────
@router.get("/session/{session_id}/audio/{question_id}")
async def get_audio(
    session_id: UUID,
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserResponse.audio_url).where(
            UserResponse.session_id == session_id,
            UserResponse.question_id == question_id,
        )
    )
    audio_url = result.scalar_one_or_none()
    if not audio_url:
        raise HTTPException(status_code=404, detail="Audio not found")
    return {"audio_url": audio_url}