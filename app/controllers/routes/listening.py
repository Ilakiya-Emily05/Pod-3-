from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.listening import (
    ListeningAssessmentCreate,
    ListeningAssessmentRead,
    ListeningAssessmentUpdate,
    ListeningAttemptAnswerCreate,
    ListeningAttemptCreate,
    ListeningAttemptRead,
)
from app.services.listening_service import ListeningService

router = APIRouter(prefix="/listening", tags=["listening"])


@router.post(
    "/assessments",
    response_model=ListeningAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_listening_assessment(
    payload: ListeningAssessmentCreate,
    db: AsyncSession = Depends(get_db),
) -> ListeningAssessmentRead:
    service = ListeningService(db)
    assessment = await service.create_assessment(payload)
    return ListeningAssessmentRead.model_validate(assessment)


@router.get("/assessments", response_model=list[ListeningAssessmentRead])
async def list_listening_assessments(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ListeningAssessmentRead]:
    service = ListeningService(db)
    assessments = await service.list_assessments(is_active=is_active)
    return [ListeningAssessmentRead.model_validate(item) for item in assessments]


@router.get("/assessments/{assessment_id}", response_model=ListeningAssessmentRead)
async def get_listening_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ListeningAssessmentRead:
    service = ListeningService(db)
    assessment = await service.get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listening assessment not found",
        )
    return ListeningAssessmentRead.model_validate(assessment)


@router.patch("/assessments/{assessment_id}", response_model=ListeningAssessmentRead)
async def update_listening_assessment(
    assessment_id: UUID,
    payload: ListeningAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ListeningAssessmentRead:
    service = ListeningService(db)
    assessment = await service.update_assessment(assessment_id, payload)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listening assessment not found",
        )
    return ListeningAssessmentRead.model_validate(assessment)


@router.post("/attempts", response_model=ListeningAttemptRead, status_code=status.HTTP_201_CREATED)
async def create_listening_attempt(
    payload: ListeningAttemptCreate,
    db: AsyncSession = Depends(get_db),
) -> ListeningAttemptRead:
    service = ListeningService(db)
    try:
        attempt = await service.create_attempt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ListeningAttemptRead.model_validate(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=ListeningAttemptRead)
async def submit_listening_attempt(
    attempt_id: UUID,
    answers: list[ListeningAttemptAnswerCreate],
    db: AsyncSession = Depends(get_db),
) -> ListeningAttemptRead:
    service = ListeningService(db)
    try:
        attempt = await service.submit_attempt(attempt_id, answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listening attempt not found"
        )

    return ListeningAttemptRead.model_validate(attempt)
