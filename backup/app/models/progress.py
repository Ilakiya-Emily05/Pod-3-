from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserProgress(Base):
    """Track user progress through learning modules."""

    __tablename__ = "user_progress"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    module_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # reading, listening, grammar
    module_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress, completed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    total_questions: Mapped[int | None] = mapped_column(nullable=True)
    correct_answers: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("user_id", "module_type", "module_id", name="uq_user_module"),
    )

    # Relationships
    user = relationship("User", back_populates="progress_records")

    def __repr__(self) -> str:
        return f"<UserProgress(user_id={self.user_id}, module={self.module_type}, status={self.status})>"
