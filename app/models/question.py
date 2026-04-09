<<<<<<< HEAD
from uuid import uuid4
=======
from sqlalchemy import JSON, Column, Integer, String
>>>>>>> origin/development

from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.config.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    question_text = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    subtopic = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(String, nullable=False)