import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class KeySkill(Base):
    __tablename__ = "key_skills"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    keyword: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="skill", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("key_skills.id"))
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON, default=list, server_default='[]')
    answer_key: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    skill = relationship("KeySkill", back_populates="questions")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="active")       # active | completed
    interview_type: Mapped[str] = mapped_column(String, default="technical")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)   # Gap Analysis

    # ── Timestamps ──────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Scores ──────────────────────────────────────────────────────
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    improvement_delta: Mapped[float | None] = mapped_column(Float, nullable=True)  # vs prev session
    duration_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)

    responses = relationship("UserResponse", back_populates="session", cascade="all, delete-orphan")


class UserResponse(Base):
    __tablename__ = "user_responses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("interview_sessions.id"), nullable=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"))

    # ── Answer ──────────────────────────────────────────────────────
    user_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Audio / Confidence ──────────────────────────────────────────
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # recording link per answer

    # ── Timestamps & Position ───────────────────────────────────────
    question_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # order in session
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_taken_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="responses")
    question = relationship("Question")