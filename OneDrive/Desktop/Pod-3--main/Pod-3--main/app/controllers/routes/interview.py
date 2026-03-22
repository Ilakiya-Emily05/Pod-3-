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
    SubmitInterviewAnswer,
)
from app.services.interview_service import (
    get_session_feedback,
    start_interview_session,
    submit_interview_answer,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/sessions", response_model=InterviewSessionOut)
async def start_session(
    payload: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Starts a new interview session and returns the first question.
    """
    result = await start_interview_session(db, payload.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "session_id": result["session"].id,
        "status": result["session"].status,
        "current_question": result["current_question"],
    }


@router.post("/sessions/{session_id}/answer", response_model=InterviewAnswerResponse)
async def submit_answer(
    session_id: UUID,
    user_answer: str | None = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Submits an answer (Audio or Text).
    Returns the next question or indicates the session is complete.
    """
    tmp_path = None
    if file:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

    try:
        result = await submit_interview_answer(
            db, 
            session_id, 
            user_answer=user_answer, 
            audio_path=tmp_path
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/sessions/{session_id}/feedback", response_model=GapAnalysisFeedback)
async def get_feedback(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Fetches the final Gap Analysis report for a completed session.
    """
    result = await get_session_feedback(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
