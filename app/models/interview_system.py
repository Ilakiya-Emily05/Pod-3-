import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class DifficultyLevel(enum.StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class KeySkill(Base):
    __tablename__ = "key_skills"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    keyword: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    questions = relationship("Question", back_populates="skill", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("key_skills.id"))
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    answer_key: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    skill = relationship("KeySkill", back_populates="questions")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    interview_type: Mapped[str | None] = mapped_column(String, nullable=True, default="general")
    status: Mapped[str] = mapped_column(String, default="active")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    improvement_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    responses = relationship("UserResponse", back_populates="session", cascade="all, delete-orphan")


class UserResponse(Base):
    __tablename__ = "user_responses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("interview_sessions.id"), nullable=True
    )
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"))
    question_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    pronunciation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pronunciation_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_taken_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session = relationship("InterviewSession", back_populates="responses")
    question = relationship("Question")
