from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base


class SessionAnalytics(Base):
    __tablename__ = "session_analytics"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_time_mins: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    best_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    worst_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    most_practiced_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserMilestone(Base):
    __tablename__ = "user_milestones"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    milestone_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    milestone_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("interview_sessions.id"), nullable=True)


class SkillScoreHistory(Base):
    __tablename__ = "skill_scores_history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    skill_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("interview_sessions.id"), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)