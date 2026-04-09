import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class UserPronunciationProfile(Base):
    __tablename__ = "user_pronunciation_profile"

    # Auto-generate both primary key and user_id UUIDs
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)

    current_level = Column(String(20), default="basic", nullable=False)
    overall_score_avg = Column(Numeric(5, 2), default=0)
    exercises_completed = Column(Integer, default=0, nullable=False)
    time_spent_total_secs = Column(Integer, default=0, nullable=False)

    weak_phonemes = Column(JSONB, default=list)
    strong_phonemes = Column(JSONB, default=list)
    level_progress = Column(JSONB, default=dict)

    last_practice_at = Column(DateTime(timezone=True))
    current_question = Column(String, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )

    phoneme_stats = relationship(
        "PhonemePerformance",
        back_populates="profile",
        cascade="all, delete-orphan",
        primaryjoin="UserPronunciationProfile.user_id == PhonemePerformance.user_id",
        foreign_keys="[PhonemePerformance.user_id]",
    )


class PhonemePerformance(Base):
    __tablename__ = "phoneme_performance"
    __table_args__ = (UniqueConstraint("user_id", "phoneme", name="uq_user_phoneme"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phoneme = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    accuracy_pct = Column(Numeric(5, 2), default=0)
    last_attempted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile = relationship(
        "UserPronunciationProfile",
        back_populates="phoneme_stats",
        primaryjoin="PhonemePerformance.user_id == UserPronunciationProfile.user_id",
        foreign_keys="[PhonemePerformance.user_id]",
    )
