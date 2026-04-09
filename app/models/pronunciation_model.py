from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class PronunciationResult(Base):
    __tablename__ = "pronunciation_results"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)

    reference_text: Mapped[str] = mapped_column(String, nullable=False)
    transcript: Mapped[str] = mapped_column(String, nullable=False)
    pronunciation_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_mistakes: Mapped[int] = mapped_column(Integer, default=0)
    mistakes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    improvement_tips: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
