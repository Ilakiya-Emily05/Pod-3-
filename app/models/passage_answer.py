from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PassageAnswer(Base, TimestampMixin):
    __tablename__ = "passage_answers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("passage_sessions.id"), nullable=False, index=True)
    question_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("comprehension_questions.id"), nullable=False, index=True)
    selected_answer: Mapped[str] = mapped_column(String, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
