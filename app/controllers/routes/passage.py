from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.utils.auth import get_current_user 
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
from app.models.user import User


router = APIRouter(prefix="/reading", tags=["Reading"])


@router.post("/start", response_model=PassageStartResponse)
async def start_reading(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserActivityService(db).record_activity(current_user.id)
    service = PassageService(db)
    return await service.start_reading(current_user.id, background_tasks)


@router.get("/{session_id}/passage", response_model=PassageResponse)
<<<<<<< Updated upstream
def get_passage(
    session_id: int,
=======
async def get_passage(
    session_id: UUID,
>>>>>>> Stashed changes
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserActivityService(db).record_activity(current_user.id)
    service = PassageService(db)
    return service.get_passage(session_id)


@router.get("/{session_id}/questions", response_model=list[PassageQuestion])
<<<<<<< Updated upstream
def get_questions(
    session_id: int,
=======
async def get_questions(
    session_id: UUID,
>>>>>>> Stashed changes
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserActivityService(db).record_activity(current_user.id)
    service = PassageService(db)
    return service.get_questions(session_id, background_tasks)


@router.post("/answer", response_model=PassageAnswerResponse)
def submit_answer(
    answer: PassageAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserActivityService(db).record_activity(current_user.id)
    service = PassageService(db)
    return service.submit_answer(answer, current_user.id)


@router.get("/{session_id}/summary", response_model=PassageSummaryResponse)
<<<<<<< Updated upstream
def get_summary(
    session_id: int,
=======
async def get_summary(
    session_id: UUID,
>>>>>>> Stashed changes
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PassageService(db)
    return service.get_summary(session_id)
