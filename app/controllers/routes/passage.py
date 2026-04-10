from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.schemas.passage_schema import (
    PassageAnswerRequest,
    PassageAnswerResponse,
    PassageQuestion,
    PassageResponse,
    PassageStartResponse,
    PassageSummaryResponse,
)
from app.services.passage_service import PassageService
from app.services.user_activity_service import UserActivityService
from app.utils.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/reading", tags=["Reading"])


# =========================
# START SESSION
# =========================
@router.post("/start", response_model=PassageStartResponse)
async def start_reading(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    UserActivityService(db).record_activity(current_user.user_id)
    service = PassageService(db)
    return await service.start_reading(current_user.user_id, background_tasks)


# =========================
# GET PASSAGE
# =========================
@router.get("/{session_id}/passage", response_model=PassageResponse)
async def get_passage(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    UserActivityService(db).record_activity(current_user.user_id)
    service = PassageService(db)
    return await service.get_passage(session_id)


# =========================
# GET QUESTIONS
# =========================
@router.get("/{session_id}/questions", response_model=list[PassageQuestion])
async def get_questions(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    UserActivityService(db).record_activity(current_user.user_id)
    service = PassageService(db)
    return await service.get_questions(session_id, background_tasks)


# =========================
# SUBMIT ANSWER
# =========================
@router.post("/answer", response_model=PassageAnswerResponse)
async def submit_answer(
    answer: PassageAnswerRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    UserActivityService(db).record_activity(current_user.user_id)
    service = PassageService(db)
    return await service.submit_answer(answer, current_user.user_id)


# =========================
# GET SUMMARY
# =========================
@router.get("/{session_id}/summary", response_model=PassageSummaryResponse)
async def get_summary(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    service = PassageService(db)
    return await service.get_summary(session_id)
