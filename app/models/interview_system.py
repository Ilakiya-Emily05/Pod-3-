import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class KeySkill(Base):
    __tablename__ = "key_skills"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)  # Placeholder for user identification
    keyword: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship to questions generated for this skill
    questions = relationship("Question", back_populates="skill", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("key_skills.id"))
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON, default=list, server_default='[]')
    answer_key: Mapped[str] = mapped_column(Text)  # The letter (A, B, C, D) or full text of the correct answer
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    skill = relationship("KeySkill", back_populates="questions")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="active")  # active, completed
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # The final "Gap Analysis"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    responses = relationship("UserResponse", back_populates="session", cascade="all, delete-orphan")


class UserResponse(Base):
    __tablename__ = "user_responses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("interview_sessions.id"), nullable=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"))
    user_answer: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    audio_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI feedback for this specific answer
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="responses")
    question = relationship("Question")
