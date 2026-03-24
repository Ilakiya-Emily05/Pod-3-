from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.grammar import (
    GrammarAssessmentCreate,
    GrammarAssessmentRead,
    GrammarAssessmentUpdate,
    GrammarAttemptAnswerCreate,
    GrammarAttemptCreate,
    GrammarAttemptRead,
)
from app.services.grammar_service import GrammarService
from app.utils.auth import (
    CurrentUser,
    get_current_admin_email,
    get_current_user,
    get_current_user_id,
)

router = APIRouter(prefix="/grammar", tags=["grammar"])


@router.post(
    "/assessments",
    response_model=GrammarAssessmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin_email)],
)
async def create_grammar_assessment(
    payload: GrammarAssessmentCreate,
    db: AsyncSession = Depends(get_db),
) -> GrammarAssessmentRead:
    service = GrammarService(db)
    assessment = await service.create_assessment(payload)
    return GrammarAssessmentRead.model_validate(assessment)


@router.get("/assessments", response_model=list[GrammarAssessmentRead])
async def list_grammar_assessments(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[GrammarAssessmentRead]:
    service = GrammarService(db)
    assessments = await service.list_assessments(is_active=is_active)
    return [GrammarAssessmentRead.model_validate(item) for item in assessments]


@router.get("/assessments/{assessment_id}", response_model=GrammarAssessmentRead)
async def get_grammar_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> GrammarAssessmentRead:
    service = GrammarService(db)
    assessment = await service.get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grammar assessment not found"
        )
    return GrammarAssessmentRead.model_validate(assessment)


@router.patch(
    "/assessments/{assessment_id}",
    response_model=GrammarAssessmentRead,
    dependencies=[Depends(get_current_admin_email)],
)
async def update_grammar_assessment(
    assessment_id: UUID,
    payload: GrammarAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> GrammarAssessmentRead:
    service = GrammarService(db)
    assessment = await service.update_assessment(assessment_id, payload)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grammar assessment not found"
        )
    return GrammarAssessmentRead.model_validate(assessment)


@router.post("/attempts", response_model=GrammarAttemptRead, status_code=status.HTTP_201_CREATED)
async def create_grammar_attempt(
    payload: GrammarAttemptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> GrammarAttemptRead:
    # Override user_id and user_email from the authenticated user context
    payload = payload.model_copy(
        update={
            "user_id": current_user.user_id,
            "user_email": current_user.email,
        }
    )
    service = GrammarService(db)
    try:
        attempt = await service.create_attempt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return GrammarAttemptRead.model_validate(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=GrammarAttemptRead)
async def submit_grammar_attempt(
    attempt_id: UUID,
    answers: list[GrammarAttemptAnswerCreate],
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> GrammarAttemptRead:
    service = GrammarService(db)
    try:
        attempt = await service.submit_attempt(attempt_id, answers, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grammar attempt not found"
        )

    return GrammarAttemptRead.model_validate(attempt)
