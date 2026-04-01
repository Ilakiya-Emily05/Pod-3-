from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


class BehavQuestion(Base):
    __tablename__ = "behav_questions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_text: Mapped[str] = mapped_column(Text)
    trait_type: Mapped[str] = mapped_column(String)  # HEXACO trait name

    options: Mapped[list["BehavOption"]] = relationship("BehavOption", back_populates="question")


class BehavOption(Base):
    __tablename__ = "behav_options"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("behav_questions.id"))
    option_key: Mapped[str] = mapped_column(String)
    option_text: Mapped[str] = mapped_column(Text)

    question: Mapped["BehavQuestion"] = relationship("BehavQuestion", back_populates="options")
    scores: Mapped[list["BehavOptionScore"]] = relationship(
        "BehavOptionScore", back_populates="option"
    )


class BehavOptionScore(Base):
    __tablename__ = "behav_option_scores"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    option_id: Mapped[int] = mapped_column(Integer, ForeignKey("behav_options.id"))

    trait_name: Mapped[str] = mapped_column(String)
    score_value: Mapped[int] = mapped_column(Integer)

    option: Mapped["BehavOption"] = relationship("BehavOption", back_populates="scores")


class BehavAttempt(Base):
    __tablename__ = "behav_attempts"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    status: Mapped[AttemptStatus] = mapped_column(String, default=AttemptStatus.IN_PROGRESS)

    # Store finalized results
    overall_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    answers: Mapped[list["BehavUserAnswer"]] = relationship(
        "BehavUserAnswer", back_populates="attempt"
    )


class BehavUserAnswer(Base):
    __tablename__ = "behav_user_answers"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("behav_attempts.id")
    )
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("behav_questions.id"))
    option_id: Mapped[int] = mapped_column(Integer, ForeignKey("behav_options.id"))
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), index=True)  # Kept for backward compatibility
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    attempt: Mapped["BehavAttempt"] = relationship("BehavAttempt", back_populates="answers")
