from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.behav_assessment_schemas import (
    AnswerRequest,
    AssessmentSessionResponse,
    BehavioralCompleteRequest,
    BehavioralCompleteResponse,
    BehavioralProfileResponse,
    ModuleRecommendation,
    QuestionResponse,
)
from app.services import behav_assessment_service
from app.services.behav_learning_hook import behav_learning_service

router = APIRouter(prefix="/behavioral", tags=["behavioral-assessment"])


async def get_dummy_user_id() -> UUID:
    """Returns a static dummy user ID for local testing."""
    return UUID("00000000-0000-0000-0000-000000000000")


@router.get("/questions", response_model=AssessmentSessionResponse)
async def fetch_questions(
    db: AsyncSession = Depends(get_db),
    # user_id: UUID = Depends(get_current_user_id),
    user_id: UUID = Depends(get_dummy_user_id),
) -> dict[str, Any]:
    # user_id = UUID("00000000-0000-0000-0000-000000000000")  # Temporary bypass
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
async def submit_questions(
    request: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    # user_id: UUID = Depends(get_current_user_id),
    user_id: UUID = Depends(get_dummy_user_id),
) -> dict[str, Any]:
    """
    Records multiple answers for a specific attempt.
    """
    await behav_assessment_service.submit_bulk_answers(db, request.attempt_id, request.answers)
    return {"message": f"{len(request.answers)} answers recorded"}


@router.get("/adaptive-questions", response_model=list[QuestionResponse])
async def get_adaptive_questions(
    attempt_id: UUID = Query(...),
    weak_traits: list[str] = Query(...),
    db: AsyncSession = Depends(get_db),
    # user_id: UUID = Depends(get_current_user_id),
    user_id: UUID = Depends(get_dummy_user_id),
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


@router.post("/complete", response_model=BehavioralCompleteResponse)
async def complete_behavioral_assessment(
    request: BehavioralCompleteRequest,
    db: AsyncSession = Depends(get_db),
    # user_id: UUID = Depends(get_current_user_id),
    user_id: UUID = Depends(get_dummy_user_id),
) -> BehavioralCompleteResponse:
    """
    Triggered on assessment finish to analyze personality and recommend learning modules.
    """
    return await behav_learning_service.process_assessment_completion(
        db, request.user_id, request.session_id
    )


@router.get("/profile/{user_id}", response_model=BehavioralProfileResponse)
async def get_behavioral_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: UUID = Depends(get_current_user_id),
    current_user: UUID = Depends(get_dummy_user_id),
) -> BehavioralProfileResponse:
    """
    Returns user's behavioral profile for dashboard display.
    """
    return await behav_learning_service.get_user_profile(db, user_id)


@router.get("/recommendations/{user_id}", response_model=list[ModuleRecommendation])
async def get_behavioral_recommendations(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: UUID = Depends(get_current_user_id),
    current_user: UUID = Depends(get_dummy_user_id),
) -> list[ModuleRecommendation]:
    """
    Returns behavioral-based module recommendations.
    """
    return await behav_learning_service.get_recommendations(db, user_id)
