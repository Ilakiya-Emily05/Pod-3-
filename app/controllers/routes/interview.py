from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.interview_system import InterviewSession, UserResponse
from app.services.interview_service import (
    get_improvement_history,
    get_session_result,
    get_user_sessions,
)

router = APIRouter(prefix="/api/v1/interview", tags=["Interview History"])


@router.get("/history/{user_id}")
async def history(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    interview_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    sort: str = Query("date_desc"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns paginated list of past interviews with summary."""
    return await get_user_sessions(
        db,
        user_id=user_id,
        page=page,
        limit=limit,
        interview_type=interview_type,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )


@router.get("/session/{session_id}/replay")
async def replay(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns full session data for replay/review."""
    return await get_session_result(db, session_id)


@router.get("/progress/{user_id}")
async def progress(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns improvement tracking data."""
    return await get_improvement_history(db, user_id)


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete a session."""
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Session already deleted.")

    await db.execute(
        update(InterviewSession)
        .where(InterviewSession.id == session_id)
        .values(deleted_at=datetime.utcnow())
    )
    await db.commit()


@router.get("/session/{session_id}/audio/{question_id}")
async def get_audio(
    session_id: UUID,
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Stream audio recording for a specific question."""
    result = await db.execute(
        select(UserResponse.audio_url).where(
            UserResponse.session_id == session_id,
            UserResponse.question_id == question_id,
        )
    )
    audio_url = result.scalar_one_or_none()
    if not audio_url:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return {"audio_url": audio_url}
