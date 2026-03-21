from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import tempfile

from app.config.database import get_db
from app.models.interview_system import DifficultyLevel
from app.schemas.interview import (
    PracticeAnswerFeedback,
    QuestionOut,
    SubmitPracticeAnswer,
)
from app.services.interview_service import get_practice_question, submit_practice_answer

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/questions/start", response_model=QuestionOut)
async def start_practice(
    user_id: str,
    difficulty: DifficultyLevel | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Section 1: AI Practice.
    Starts the practice section by fetching a question for the user.
    If no difficulty is provided, it is determined by performance.
    """
    question = await get_practice_question(db, user_id, difficulty)
    if not question:
        raise HTTPException(
            status_code=404, detail="No questions found for this user."
        )
    return question


@router.post("/answer", response_model=PracticeAnswerFeedback)
async def submit_answer(
    user_id: str = Form(...),
    question_id: UUID = Form(...),
    user_answer: str | None = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Section 1: AI Practice.
    Submits an answer (Audio or Text).
    """
    tmp_path = None
    if file:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

    try:
        result = await submit_practice_answer(
            db, user_id, question_id, user_answer=user_answer, audio_path=tmp_path
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
