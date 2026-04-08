from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user import User
from app.schemas.question_schema import QuestionResponse
from app.schemas.summary_schema import TestSummaryResponse
from app.schemas.test_session_schema import AnswerRequest, AnswerResponse, TestSessionResponse
from app.services.test_service import TestService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/start", response_model=TestSessionResponse)
def start_test(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TestSessionResponse:
    service = TestService(db)
    return service.start_test(current_user.id)


@router.get("/question", response_model=QuestionResponse)
def get_question(
    session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> QuestionResponse:
    service = TestService(db)
    return service.get_next_question(session_id)


@router.get("/questionsbytopic", response_model=list[QuestionResponse])
def get_questions_by_topic(
    topic: str, subtopic: str, db: Session = Depends(get_db)
) -> list[QuestionResponse]:
    service = TestService(db)
    return service.get_questions_by_topic(topic, subtopic)


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(
    answer: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerResponse:
    service = TestService(db)
    return service.submit_answer(answer.session_id, answer.question_id, answer.selected_answer)


@router.get("/{session_id}/summary", response_model=TestSummaryResponse)
def get_test_summary(
    session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TestSummaryResponse:
    service = TestService(db)
    return service.get_summary(session_id, current_user.id)
