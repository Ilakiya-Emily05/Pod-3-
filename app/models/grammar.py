from __future__ import annotations

from datetime import datetime  # noqa: TC003
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.assessment_status import AttemptStatus
from app.models.base import Base, TimestampMixin


class GrammarAssessment(Base, TimestampMixin):
    __tablename__ = "grammar_assessments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    questions: Mapped[list[GrammarQuestion]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="GrammarQuestion.sort_order",
    )
    attempts: Mapped[list[GrammarAttempt]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class GrammarQuestion(Base, TimestampMixin):
    __tablename__ = "grammar_questions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("1.00"))

    assessment: Mapped[GrammarAssessment] = relationship(back_populates="questions")
    options: Mapped[list[GrammarQuestionOption]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="GrammarQuestionOption.sort_order",
    )
    submitted_answers: Mapped[list[GrammarAttemptAnswer]] = relationship(back_populates="question")


class GrammarQuestionOption(Base, TimestampMixin):
    __tablename__ = "grammar_question_options"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped[GrammarQuestion] = relationship(back_populates="options")
    selected_in_answers: Mapped[list[GrammarAttemptAnswer]] = relationship(
        back_populates="selected_option"
    )


class GrammarAttempt(Base, TimestampMixin):
    __tablename__ = "grammar_attempts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="assessment_attempt_status_enum", create_type=False),
        nullable=False,
        default=AttemptStatus.IN_PROGRESS,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("0.00"))

    assessment: Mapped[GrammarAssessment] = relationship(back_populates="attempts")
    answers: Mapped[list[GrammarAttemptAnswer]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class GrammarAttemptAnswer(Base):
    __tablename__ = "grammar_attempt_answers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_option_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grammar_question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    attempt: Mapped[GrammarAttempt] = relationship(back_populates="answers")
    question: Mapped[GrammarQuestion] = relationship(back_populates="submitted_answers")
    selected_option: Mapped[GrammarQuestionOption | None] = relationship(
        back_populates="selected_in_answers"
    )
