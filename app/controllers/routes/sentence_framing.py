import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.sentence_framing import (
    SentenceFramingRead,
    SentenceGenerateRequest,
    SentenceSubmissionCreate,
    SentenceSubmissionRead,
)
from app.services.sentence_framing_service import SentenceFramingService
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/sentence-framing", tags=["sentence-framing"])
logger = logging.getLogger(__name__)


@router.get("/exercises", response_model=None)
async def list_sentence_categories(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Returns a unified list of categories and subcategories.
    Each subcategory includes an 'exercise_id' trigger for dynamic generation.
    """
    service = SentenceFramingService(db)
    return {"categories": await service.get_categories()}


@router.get("/exercise/{exercise_id}", response_model=SentenceFramingRead)
async def get_sentence_exercise(
    exercise_id: UUID,
    cefr_level: str = Query("B1", description="Target CEFR level (A1-C2)"),
    topic: str | None = Query(None, description="Optional custom topic for the exercise"),
    difficulty: str = Query("Professional", description="Difficulty level"),
    industry: str = Query("General Professional", description="Professional industry context"),
    exercise_type: str = Query("fill_in_blank", description="Type of exercise"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Generates a dynamic AI exercise based on a subcategory trigger (exercise_id).
    Accepts query parameters for on-the-fly customization.
    """
    service = SentenceFramingService(db)
    params = SentenceGenerateRequest(
        cefr_level=cefr_level,
        topic=topic,
        difficulty=difficulty,
        industry=industry,
        exercise_type=exercise_type,
    )
    try:
        exercise = await service.get_exercise(exercise_id, params=params)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exercise category not found"
            )
        return SentenceFramingRead.model_validate(exercise)
    except Exception as e:
        logger.error(f"Sentence exercise generation failed: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during exercise generation.",
        )


@router.post("/submit", response_model=SentenceSubmissionRead, status_code=status.HTTP_201_CREATED)
async def submit_sentence_response(
    payload: SentenceSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Submits a user response for evaluation against the dynamically generated exercise.
    Evaluation is AI-driven and CEFR-mapped.
    """
    service = SentenceFramingService(db)
    try:
        submission = await service.submit_response(user_id, payload)
        return SentenceSubmissionRead.model_validate(submission)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Sentence submission failed: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during submission processing.",
        )


@router.get("/progress/{user_id}")
async def get_sentence_progress(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id),
):
    """
    Returns user progress for the Sentence Framing module.
    """
    service = SentenceFramingService(db)
    return await service.get_user_progress(user_id)
