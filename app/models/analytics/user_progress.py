from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserModuleProgress(Base):
    __tablename__ = "user_topic_progress"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    module_name: Mapped[str] = mapped_column(String(50))
    topic: Mapped[str] = mapped_column(String(100))
    subtopic: Mapped[str] = mapped_column(String(100))

    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_pct: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0)

    time_spent_secs: Mapped[int] = mapped_column(Integer, default=0)
    mastery_achieved: Mapped[bool] = mapped_column(Boolean, default=False)

    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="progress_records")

    __table_args__ = (
        UniqueConstraint("user_id", "module_name", "topic", "subtopic", name="uq_user_module"),
    )


__all__ = ["UserModuleProgress"]
