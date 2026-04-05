from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.question import Question
from app.models.user_answer import UserAnswer


class UserAnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user_answer(self, session_id: UUID, question_id: UUID, selected_answer: str, is_correct: bool) -> UserAnswer:
        user_answer = UserAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )
        self.db.add(user_answer)
        self.db.commit()
        self.db.refresh(user_answer)
        return user_answer

    def get_answers_by_session(self, session_id: UUID) -> list[UserAnswer]:
        return self.db.query(UserAnswer).options(joinedload(UserAnswer.question)).filter(UserAnswer.session_id == session_id).all()

    def get_attempted_question_ids(self, session_id: UUID) -> list[UUID]:
        results = self.db.query(UserAnswer.question_id).filter(UserAnswer.session_id == session_id).all()
        return [r.question_id for r in results]

    def count_attempted(self, session_id: UUID, topic: str, subtopic: str) -> int:
        return self.db.query(UserAnswer).join(Question, UserAnswer.question_id == Question.id).filter(UserAnswer.session_id == session_id, Question.topic == topic, Question.subtopic == subtopic).count()
