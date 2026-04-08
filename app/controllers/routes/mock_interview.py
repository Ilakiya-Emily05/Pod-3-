"""Mock Interview routes — Section 2 of the interview flow."""

import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.interview_service import (
    get_session_feedback,
    start_interview_session,
    submit_batch_answer,
)
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/mock", tags=["Mock Interview"])


@router.post("/sessions")
async def start_session(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a new mock interview session. Returns first question."""
    return await start_interview_session(db, str(user_id))


@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: UUID,
    user_answer: str | None = Form(None),
    file: UploadFile | None = File(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Submit an answer (text or audio) for the current question.
    Returns next question or session_complete flag with pronunciation feedback.
    Temp file is always cleaned up via finally block.
    """
    tmp_path: str | None = None

    if file and file.filename:
        suffix = os.path.splitext(file.filename)[1].lower() or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

    try:
        return await submit_batch_answer(
            db,
            session_id=session_id,
            audio_path=tmp_path,
            user_answer=user_answer,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/sessions/{session_id}/feedback")
async def get_feedback(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns final Gap Analysis for a completed session."""
    return await get_session_feedback(db, session_id)
