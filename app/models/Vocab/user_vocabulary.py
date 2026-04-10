from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class UserVocabulary(Base):
    __tablename__ = "user_vocabulary"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)

    word_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vocabulary_words.word_id"), nullable=False, index=True
    )

    retention_score: Mapped[float] = mapped_column(Float, default=2.5)  # easiness factor
    repetition_count: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)

    next_review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_incorrect: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(20), default="learning")
    # values: learning / mastered / struggling

    last_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "word_id", name="uq_user_word"),)
