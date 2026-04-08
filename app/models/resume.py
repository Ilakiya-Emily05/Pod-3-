from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, Float, JSON, Index, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_kb: Mapped[float | None] = mapped_column(Float, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    parse_status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    experience: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    education: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    certifications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    projects: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    languages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    achievements: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    suggested_roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    primary_tech_stack: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    interview_topics: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    strength_areas: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    gap_areas: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    __table_args__ = (
        Index("ix_resumes_email", "email"),
        Index("ix_resumes_uploaded_at", "uploaded_at"),
        Index("ix_resumes_experience_level", "experience_level"),
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id} name={self.full_name!r}>"