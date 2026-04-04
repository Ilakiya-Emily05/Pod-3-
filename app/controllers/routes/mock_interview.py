from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import tempfile

from app.config.database import get_db
from app.schemas.interview import (
    GapAnalysisFeedback,
    InterviewAnswerResponse,
    InterviewSessionOut,
    StartInterviewRequest,
)
from app.services.interview_service import (
    get_session_feedback,
    start_interview_session,
    submit_batch_answer,
)

router = APIRouter(prefix="/mock", tags=["Mock Interview"])


# ── Start Session ─────────────────────────────────────────────────
@router.post("/sessions", response_model=InterviewSessionOut)
async def start_session(
    payload: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a new mock interview session. Returns first question."""
    result = await start_interview_session(db, payload.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "session_id": result["session"].id,
        "status": result["session"].status,
        "current_question": result["current_question"],
    }


# ── Submit Answer ─────────────────────────────────────────────────
@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: UUID,
    user_answer: str | None = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    """Submit answer (text or audio). Returns next question or session complete."""
    tmp_path = None
    if file:
        suffix = os.path.splitext(file.filename or "audio.webm")[1].lower() or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

    try:
        result = await submit_batch_answer(
            db, session_id, audio_path=tmp_path,user_answer=user_answer
            )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Get Feedback ──────────────────────────────────────────────────
@router.get("/sessions/{session_id}/feedback", response_model=GapAnalysisFeedback)
async def get_feedback(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns final Gap Analysis for a completed session."""
    result = await get_session_feedback(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result