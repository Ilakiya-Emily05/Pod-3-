from sqlalchemy.orm import Session
from uuid import UUID

from app.models.test_session import TestSession


class TestSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: UUID, topic: str, subtopic: str) -> TestSession:
        session = TestSession(
            user_id=user_id,
            current_topic=topic,
            current_subtopic=subtopic,
            question_index=0,
            correct_count=0,
            total_questions=0,
            status="IN_PROGRESS",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: int) -> TestSession | None:
        return self.db.query(TestSession).filter(TestSession.id == session_id).first()

    def get_active_session(self, user_id: UUID) -> TestSession | None:
        return self.db.query(TestSession).filter(TestSession.user_id == user_id, TestSession.status == "IN_PROGRESS").first()

    def update(self, session: TestSession) -> TestSession:
        self.db.commit()
        self.db.refresh(session)
        return session
