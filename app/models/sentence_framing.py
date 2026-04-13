from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.assessment_status import CEFRLevel
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SentenceExercise(Base, TimestampMixin):
    __tablename__ = "sentence_exercises"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    exercise_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'fill_in_blank', 'reorder', 'free_form'
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    cefr_level: Mapped[CEFRLevel | None] = mapped_column(
        Enum(CEFRLevel, name="cefr_level_enum", create_type=False),
        nullable=True,
    )
    difficulty_score: Mapped[float | None] = mapped_column(NUMERIC(6, 2), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # stores sender_role, recipient, tone
    template: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # for fill-in-blank or reorder
    hints: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    example_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_secs: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    submissions: Mapped[list[SentenceSubmission]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
    )


class SentenceSubmission(Base, TimestampMixin):
    __tablename__ = "user_sentence_submissions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sentence_exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    structure_score: Mapped[int] = mapped_column(Integer, nullable=False)
    tone_score: Mapped[int] = mapped_column(Integer, nullable=False)
    grammar_score: Mapped[int] = mapped_column(Integer, nullable=False)
    content_score: Mapped[int] = mapped_column(Integer, nullable=False)
    cefr_level: Mapped[str | None] = mapped_column(String(3), nullable=True)
    ability_score: Mapped[float | None] = mapped_column(NUMERIC(6, 4), nullable=True)
    ai_feedback: Mapped[dict] = mapped_column(JSONB, nullable=False)
    time_taken_secs: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    exercise: Mapped[SentenceExercise] = relationship(back_populates="submissions")
    user: Mapped[User] = relationship("User")  # Assuming User model exists as 'User'
