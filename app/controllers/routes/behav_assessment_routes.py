from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.behav_assessment_schemas import (
    AnswerRequest,
    AssessmentSessionResponse,
    BulkAnswerRequest,
    QuestionResponse,
    ResultResponse,
)
from app.services import behav_assessment_service
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/behav-assessment", tags=["behavioral-assessment"])


@router.get("/questions", response_model=AssessmentSessionResponse)
async def fetch_questions(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
) -> dict[str, Any]:
    #user_id = UUID("00000000-0000-0000-0000-000000000000")  # Temporary bypass
    """
    Dynamically generates 10 questions and creates a new assessment attempt.
    Returns the attempt_id and the questions.
    """
    data = await behav_assessment_service.get_dynamic_questions(db, user_id)
    questions = data["questions"]

    formatted_questions = []
    for q in questions:
        option_map = {opt.option_key: opt.option_text for opt in q.options}
        formatted_questions.append(
            {"id": q.id, "question_text": q.question_text, "options": option_map}
        )

    return {"attempt_id": data["attempt_id"], "questions": formatted_questions}


@router.post("/answer")
async def submit_answer(
    request: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """
    Records a single answer within a specific attempt.
    """
    await behav_assessment_service.submit_answer(
        db, request.attempt_id, request.question_id, request.option_key
    )
    return {"message": "Answer recorded"}


@router.post("/bulk-answer")
async def submit_bulk_answers(
    request: BulkAnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """
    Records multiple answers for a specific attempt.
    """
    await behav_assessment_service.submit_bulk_answers(db, request.attempt_id, request.answers)
    return {"message": f"{len(request.answers)} answers recorded"}


@router.get("/result", response_model=ResultResponse)
async def get_result(
    attempt_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
) -> dict[str, Any]:
    """
    Calculates or retrieves the persistent result for a specific attempt.
    """
    return await behav_assessment_service.calculate_result(db, attempt_id)


@router.get("/adaptive-questions", response_model=list[QuestionResponse])
async def get_adaptive_questions(
    attempt_id: UUID = Query(...),
    weak_traits: list[str] = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
) -> list[dict[str, Any]]:
    """
    Dynamically generates adaptive questions for identified weak traits for a specific attempt.
    """
    questions = await behav_assessment_service.get_adaptive_questions_for_attempt(
        db, attempt_id, weak_traits
    )
    result = []
    for q in questions:
        option_map = {opt.option_key: opt.option_text for opt in q.options}
        result.append({"id": q.id, "question_text": q.question_text, "options": option_map})
    return result
