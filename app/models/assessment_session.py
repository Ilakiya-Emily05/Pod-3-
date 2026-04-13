from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class AssessmentSessionType(str, enum.Enum):
    PRE_TEST = "pre_test"
    POST_TEST = "post_test"


class AssessmentSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AssessmentSection(str, enum.Enum):
    A_READING = "A"
    B_SPEAKING = "B"
    C_GRAMMAR = "C"
    D_LISTENING = "D"
    E_WRITING = "E"


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_type: Mapped[AssessmentSessionType] = mapped_column(
        Enum(AssessmentSessionType, name="assessment_session_type"),
        nullable=False,
    )

    status: Mapped[AssessmentSessionStatus] = mapped_column(
        Enum(AssessmentSessionStatus, name="assessment_session_status"),
        nullable=False,
        default=AssessmentSessionStatus.IN_PROGRESS,
    )

    current_section: Mapped[AssessmentSection] = mapped_column(
        Enum(AssessmentSection, name="assessment_section"),
        nullable=False,
        default=AssessmentSection.A_READING,
    )

    composite_cefr_result: Mapped[str | None] = mapped_column(String(20), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )