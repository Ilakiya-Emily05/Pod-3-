from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
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
    # Your advanced features
    get_improvement_history,
    get_session_feedback,
    get_session_result,
    get_user_sessions,

    # Batch interview (incoming)
    start_interview_session,
    submit_batch_answer,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


# ── Start Batch Session (5-min interview) ──────────────────────────────────────
@router.post("/sessions", response_model=BatchSessionOut)
async def start_mock_session(
    payload: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await start_batch_interview(db, payload.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Submit Batch Audio ─────────────────────────────────────────────────────────
@router.post("/sessions/{session_id}/answer")
async def submit_mock_audio(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
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


# ── List Sessions ──────────────────────────────────────────────────────────────
@router.get("/sessions", response_model=list[MockSessionOut])
async def list_mock_sessions(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await get_user_sessions(db, candidate_id)


# ── Get Session Result ─────────────────────────────────────────────────────────
@router.get("/sessions/{session_id}/result", response_model=MockSessionResultOut)
async def fetch_mock_result(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await get_session_result(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Gap Analysis Feedback ──────────────────────────────────────────────────────
@router.get("/sessions/{session_id}/feedback")
async def get_feedback(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await get_session_feedback(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Session History (paginated) ────────────────────────────────────────────────
@router.get("/history/{user_id}")
async def history(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    interview_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await get_user_sessions(
        db,
        user_id,
        page=page,
        limit=limit,
        interview_type=interview_type,
    )


# ── Session Replay ─────────────────────────────────────────────────────────────
@router.get("/sessions/{session_id}/replay")
async def replay(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await get_session_result(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Improvement History ────────────────────────────────────────────────────────
@router.get("/history/{user_id}/improvement")
async def improvement_history(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await get_improvement_history(db, user_id)