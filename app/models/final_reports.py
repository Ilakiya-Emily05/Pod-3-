"""
Final Report Model for Interview Sessions
Stores comprehensive evaluation results including scores, feedback, and analysis.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FinalReport(Base):
    """Stores final reports generated after interview sessions complete."""

    __tablename__ = "final_reports"

    report_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("interview_sessions.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    performance_level: Mapped[str] = mapped_column(String(50), default="Needs Improvement")
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    strengths: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    improvement_areas: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    skill_analysis: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    ai_narrative: Mapped[str] = mapped_column(Text, default="")
    next_steps: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    peer_comparison: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
