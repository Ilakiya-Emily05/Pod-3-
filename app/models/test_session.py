from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.config.database import Base


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_topic = Column(String, nullable=False)
    current_subtopic = Column(String, nullable=False)
    question_index = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    passed_subtopics = Column(Integer, default=0)
    failed_subtopics = Column(Integer, default=0)
    completed_subtopics = Column(Integer, default=0)
    status = Column(String, default="IN_PROGRESS")
