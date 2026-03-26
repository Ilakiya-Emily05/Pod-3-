from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import tempfile

from app.config.database import get_db
from app.schemas.interview import (
    BatchSessionOut,
    MockSessionOut,
    MockSessionResultOut,
    StartInterviewRequest,
)
from app.services.interview_service import (
    get_session_result,
    get_user_sessions,
    start_batch_interview,
    submit_batch_answer,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/sessions", response_model=BatchSessionOut)
async def start_mock_session(
    payload: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Starts a compulsory 5-minute mock session by providing 15 questions upfront.
    """
    result = await start_batch_interview(db, payload.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/answer")
async def submit_mock_audio(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Submits the single 5-minute audio file for processing.
    """
    tmp_path = None
    suffix = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = await submit_batch_answer(db, session_id, tmp_path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/sessions", response_model=list[MockSessionOut])
async def list_mock_sessions(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Lists all mock interview sessions for a specific user.
    """
    sessions = await get_user_sessions(db, candidate_id)
    return sessions


@router.get("/sessions/{session_id}/result", response_model=MockSessionResultOut)
async def fetch_mock_result(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 2: Mock Interview.
    Returns detailed results (Gap Analysis + responses) for a session.
    """
    result = await get_session_result(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
