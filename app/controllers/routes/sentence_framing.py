from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.sentence_framing import (
    CategoryRead,
    ExerciseListItem,
    SentenceExerciseRead,
    SentenceSubmissionCreate,
    SentenceSubmissionRead,
)
from app.services.sentence_framing_service import SentenceFramingService
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/sentence-framing", tags=["sentence-framing"])


async def get_dummy_user_id() -> UUID:
    """Returns a static dummy user ID for local testing."""
    return UUID("00000000-0000-0000-0000-000000000000")


@router.get("/exercises", response_model=dict[str, list[CategoryRead]])
async def list_sentence_categories(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
    # user_id: UUID = Depends(get_dummy_user_id)
):
    service = SentenceFramingService(db)
    return {"categories": await service.get_categories()}


@router.get("/exercises/subcategory/{subcategory_id}", response_model=list[ExerciseListItem])
async def list_exercises_in_subcategory(
    subcategory_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
    # user_id: UUID = Depends(get_dummy_user_id)
):
    service = SentenceFramingService(db)
    exercises = await service.get_exercises_by_subcategory(subcategory_id)
    return [ExerciseListItem.model_validate(ex) for ex in exercises]


@router.get("/exercise/{exercise_id}", response_model=SentenceExerciseRead)
async def get_sentence_exercise(
    exercise_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
    # user_id: UUID = Depends(get_dummy_user_id)
):
    service = SentenceFramingService(db)
    exercise = await service.get_exercise(exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Exercise not found"
        )
    return SentenceExerciseRead.model_validate(exercise)


@router.post(
    "/submit", 
    response_model=SentenceSubmissionRead, 
    status_code=status.HTTP_201_CREATED
)
async def submit_sentence_response(
    payload: SentenceSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
    # user_id: UUID = Depends(get_dummy_user_id)
):
    service = SentenceFramingService(db)
    try:
        submission = await service.submit_response(user_id, payload)
        return SentenceSubmissionRead.model_validate(submission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Submission failed: {str(e)}"
        )


@router.get("/progress/{user_id}")
async def get_sentence_progress(
    user_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
    # current_user: UUID = Depends(get_dummy_user_id)
):
    service = SentenceFramingService(db)
    return await service.get_user_progress(user_id)
