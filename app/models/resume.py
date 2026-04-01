import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, JSON, Index
from app.config.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Resume(Base):
    __tablename__ = "resumes"

    id           = Column(String(36),  primary_key=True, default=_new_uuid)
    user_id      = Column(String(50),  default="default_user", nullable=False)
    filename     = Column(String(255), nullable=False)
    file_size_kb = Column(Float,       nullable=True)
    uploaded_at  = Column(DateTime,    default=datetime.utcnow, nullable=False)
    parse_status = Column(String(20),  default="success", nullable=False)
    parse_error  = Column(Text,        nullable=True)
    raw_text     = Column(Text,        nullable=True)

    full_name    = Column(String(255), nullable=True)
    email        = Column(String(255), nullable=True)
    phone        = Column(String(50),  nullable=True)
    location     = Column(String(255), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    github_url   = Column(String(512), nullable=True)
    summary      = Column(Text,        nullable=True)

    skills         = Column(JSON, default=list, nullable=False)
    experience     = Column(JSON, default=list, nullable=False)
    education      = Column(JSON, default=list, nullable=False)
    certifications = Column(JSON, default=list, nullable=False)
    projects       = Column(JSON, default=list, nullable=False)
    languages      = Column(JSON, default=list, nullable=False)
    achievements   = Column(JSON, default=list, nullable=False)

    experience_level   = Column(String(20), nullable=True)
    suggested_roles    = Column(JSON, default=list, nullable=False)
    primary_tech_stack = Column(JSON, default=list, nullable=False)
    interview_topics   = Column(JSON, default=list, nullable=False)
    strength_areas     = Column(JSON, default=list, nullable=False)
    gap_areas          = Column(JSON, default=list, nullable=False)

    __table_args__ = (
        Index("ix_resumes_email",            "email"),
        Index("ix_resumes_uploaded_at",      "uploaded_at"),
        Index("ix_resumes_experience_level", "experience_level"),
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id} name={self.full_name!r}>"
