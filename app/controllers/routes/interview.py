from uuid import UUID
from app.services.interview_service import get_user_sessions
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

@router.get("/session/{session_id}/replay")
async def replay(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_session_result(db, session_id)

@router.get("/history/{user_id}")
async def history(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    interview_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    
    sessions = await get_user_sessions(db, user_id)

    
    if interview_type:
        sessions = [s for s in sessions if s.interview_type == interview_type]


    start = (page - 1) * limit
    end = start + limit

    
    return {
        "total": len(sessions),
        "page": page,
        "limit": limit,
        "sessions": [
            {
                "session_id": s.id,
                "interview_type": s.interview_type,
                "date": s.created_at,
                "duration_mins": s.duration_mins,
                "questions_count": len(s.responses),
                "overall_score": s.overall_score,
                "has_recordings": any(r.audio_url for r in s.responses),
            }
            for s in sessions[start:end]
        ]
    }