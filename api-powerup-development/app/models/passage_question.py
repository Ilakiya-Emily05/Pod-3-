from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.config.database import Base


class ComprehensionQuestion(Base):
    __tablename__ = "comprehension_questions"

    id = Column(Integer, primary_key=True, index=True)
    passage_id = Column(Integer, ForeignKey("passages.id"), nullable=False)
    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(String, nullable=False)
    difficulty = Column(String, index=True)
    explanation = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
