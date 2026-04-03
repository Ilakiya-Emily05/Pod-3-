from sqlalchemy import Column, JSON, Integer, String

from app.config.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    subtopic = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(String, nullable=False)
