from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.question_schema import QuestionResponse
from app.schemas.summary_schema import TestSummaryResponse
from app.schemas.test_session_schema import AnswerRequest, AnswerResponse, TestSessionResponse
from app.services.test_service import TestService
from app.utils.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/start", response_model=TestSessionResponse)
async def start_test(
    current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    service = TestService(db)
    return await service.start_test(current_user.user_id)


@router.get("/question", response_model=QuestionResponse)
async def get_question(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionResponse:
    service = TestService(db)
    return await service.get_next_question(session_id, current_user.user_id)


@router.get("/questionsbytopic", response_model=list[QuestionResponse])
async def get_questions_by_topic(
    topic: str, subtopic: str, db: AsyncSession = Depends(get_db)
) -> list[QuestionResponse]:
    service = TestService(db)
    return await service.get_questions_by_topic(topic, subtopic)


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    answer: AnswerRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnswerResponse:
    service = TestService(db)
    return await service.submit_answer(
        answer.session_id,
        answer.question_id,
        answer.selected_answer,
        current_user.user_id,
    )


@router.get("/{session_id}/summary", response_model=TestSummaryResponse)
async def get_test_summary(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestSummaryResponse:
    service = TestService(db)
    return await service.get_summary(session_id, current_user.user_id)
