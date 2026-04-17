from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


class BehavQuestion(Base):
    __tablename__ = "behav_questions"
    __table_args__ = {"extend_existing": True}  # ruff: noqa: RUF012

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_text: Mapped[str] = mapped_column(Text)
    trait_type: Mapped[str] = mapped_column(String)  # HEXACO trait name

    options: Mapped[list["BehavOption"]] = relationship("BehavOption", back_populates="question")


class BehavOption(Base):
    __tablename__ = "behav_options"
    __table_args__ = {"extend_existing": True}  # ruff: noqa: RUF012

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("behav_questions.id")
    )
    option_key: Mapped[str] = mapped_column(String)
    option_text: Mapped[str] = mapped_column(Text)

    question: Mapped["BehavQuestion"] = relationship("BehavQuestion", back_populates="options")
    scores: Mapped[list["BehavOptionScore"]] = relationship(
        "BehavOptionScore", back_populates="option"
    )


class BehavOptionScore(Base):
    __tablename__ = "behav_option_scores"
    __table_args__: ClassVar[dict[str, Any]] = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    option_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("behav_options.id"))

    trait_name: Mapped[str] = mapped_column(String)
    score_value: Mapped[int] = mapped_column(Integer)

    option: Mapped["BehavOption"] = relationship("BehavOption", back_populates="scores")


class BehavAttempt(Base):
    __tablename__ = "behav_attempts"
    __table_args__ = {"extend_existing": True}  # ruff: noqa: RUF012

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    status: Mapped[AttemptStatus] = mapped_column(String, default=AttemptStatus.IN_PROGRESS)

    # Store finalized results
    overall_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["BehavUserAnswer"]] = relationship(
        "BehavUserAnswer", back_populates="attempt"
    )


class BehavUserAnswer(Base):
    __tablename__ = "behav_user_answers"
    __table_args__: ClassVar[dict[str, Any]] = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    attempt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("behav_attempts.id")
    )
    question_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("behav_questions.id")
    )
    option_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("behav_options.id"))
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), index=True
    )  # Kept for backward compatibility

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    attempt: Mapped["BehavAttempt"] = relationship("BehavAttempt", back_populates="answers")


class BehavProfile(Base):
    __tablename__ = "behavioral_profiles"
    __table_args__ = {"extend_existing": True}  # ruff: noqa: RUF012

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True
    )
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("behav_attempts.id"))
    hexaco_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ai_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_modules: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    development_areas: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
