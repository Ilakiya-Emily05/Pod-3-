from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.config.database import Base


class PassageAnswer(Base):
    __tablename__ = "passage_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("passage_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("comprehension_questions.id"), nullable=False)
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
