from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, ForeignKey

from app.models.base import Base


class UserStreaks(Base):
    __tablename__ = "user_streaks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)

    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    streak_freeze_available: Mapped[bool] = mapped_column(Boolean, default=True)


__all__ = ["UserStreaks"]
