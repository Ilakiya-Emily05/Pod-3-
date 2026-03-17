from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.reading import (
    ReadingAssessmentCreate,
    ReadingAssessmentRead,
    ReadingAssessmentUpdate,
    ReadingAttemptAnswerCreate,
    ReadingAttemptCreate,
    ReadingAttemptRead,
)
from app.services.reading_service import ReadingService

router = APIRouter(prefix="/reading", tags=["reading"])


@router.post(
    "/assessments",
    response_model=ReadingAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_reading_assessment(
    payload: ReadingAssessmentCreate,
    db: AsyncSession = Depends(get_db),
) -> ReadingAssessmentRead:
    service = ReadingService(db)
    assessment = await service.create_assessment(payload)
    return ReadingAssessmentRead.model_validate(assessment)


@router.get("/assessments", response_model=list[ReadingAssessmentRead])
async def list_reading_assessments(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ReadingAssessmentRead]:
    service = ReadingService(db)
    assessments = await service.list_assessments(is_active=is_active)
    return [ReadingAssessmentRead.model_validate(item) for item in assessments]


@router.get("/assessments/{assessment_id}", response_model=ReadingAssessmentRead)
async def get_reading_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ReadingAssessmentRead:
    service = ReadingService(db)
    assessment = await service.get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading assessment not found"
        )
    return ReadingAssessmentRead.model_validate(assessment)


@router.patch("/assessments/{assessment_id}", response_model=ReadingAssessmentRead)
async def update_reading_assessment(
    assessment_id: UUID,
    payload: ReadingAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ReadingAssessmentRead:
    service = ReadingService(db)
    assessment = await service.update_assessment(assessment_id, payload)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading assessment not found"
        )
    return ReadingAssessmentRead.model_validate(assessment)


@router.post("/attempts", response_model=ReadingAttemptRead, status_code=status.HTTP_201_CREATED)
async def create_reading_attempt(
    payload: ReadingAttemptCreate,
    db: AsyncSession = Depends(get_db),
) -> ReadingAttemptRead:
    service = ReadingService(db)
    try:
        attempt = await service.create_attempt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ReadingAttemptRead.model_validate(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=ReadingAttemptRead)
async def submit_reading_attempt(
    attempt_id: UUID,
    answers: list[ReadingAttemptAnswerCreate],
    db: AsyncSession = Depends(get_db),
) -> ReadingAttemptRead:
    service = ReadingService(db)
    try:
        attempt = await service.submit_attempt(attempt_id, answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading attempt not found"
        )

    return ReadingAttemptRead.model_validate(attempt)
