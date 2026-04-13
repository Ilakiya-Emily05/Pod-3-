from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    cefr_level: Mapped[str] = mapped_column(String(10), nullable=False)
    assigned_modules: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    user_goal: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ModuleUnlock(Base):
    __tablename__ = "module_unlocks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    unlocked_level: Mapped[str] = mapped_column(String(20), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
