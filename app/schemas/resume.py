from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Nested schemas ────────────────────────────────────────────────────────────

class PersonalInfo(BaseModel):
    full_name:    Optional[str] = None
    email:        Optional[str] = None
    phone:        Optional[str] = None
    location:     Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url:   Optional[str] = None
    summary:      Optional[str] = None


class ExperienceItem(BaseModel):
    role:         Optional[str] = None
    company:      Optional[str] = None
    duration:     Optional[str] = None
    bullets:      list[str]     = Field(default_factory=list)
    technologies: list[str]     = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree:      Optional[str] = None
    years:       Optional[str] = None
    gpa:         Optional[str] = None


class CertificationItem(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None


class ProjectItem(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    tech_stack:  list[str]     = Field(default_factory=list)


class InterviewMetadata(BaseModel):
    experience_level:   Optional[str] = None
    suggested_roles:    list[str]     = Field(default_factory=list)
    primary_tech_stack: list[str]     = Field(default_factory=list)
    interview_topics:   list[str]     = Field(default_factory=list)
    strength_areas:     list[str]     = Field(default_factory=list)
    gap_areas:          list[str]     = Field(default_factory=list)


# ── Response schemas ──────────────────────────────────────────────────────────

class ResumeDetail(BaseModel):
    id:           str
    filename:     str
    file_size_kb: Optional[float] = None
    uploaded_at:  datetime
    parse_status: str
    personal:           PersonalInfo
    skills:             list[str]               = Field(default_factory=list)
    experience:         list[ExperienceItem]    = Field(default_factory=list)
    education:          list[EducationItem]     = Field(default_factory=list)
    certifications:     list[CertificationItem] = Field(default_factory=list)
    projects:           list[ProjectItem]       = Field(default_factory=list)
    languages:          list[str]               = Field(default_factory=list)
    achievements:       list[str]               = Field(default_factory=list)
    interview_metadata: InterviewMetadata

    model_config = {"from_attributes": True}


class ResumeSummary(BaseModel):
    id:               str
    filename:         str
    full_name:        Optional[str] = None
    email:            Optional[str] = None
    experience_level: Optional[str] = None
    skills_count:     int           = 0
    uploaded_at:      datetime
    parse_status:     str

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    count:   int
    resumes: list[ResumeSummary]


class UploadResponse(BaseModel):
    message: str
    resume:  ResumeDetail


class InterviewPack(BaseModel):
    resume_id:          str
    candidate_name:     Optional[str] = None
    experience_level:   Optional[str] = None
    suggested_roles:    list[str]     = Field(default_factory=list)
    primary_tech_stack: list[str]     = Field(default_factory=list)
    all_skills:         list[str]     = Field(default_factory=list)
    interview_topics:   list[str]     = Field(default_factory=list)
    strength_areas:     list[str]     = Field(default_factory=list)
    gap_areas:          list[str]     = Field(default_factory=list)
    experience_summary: list[dict]    = Field(default_factory=list)
    education_summary:  list[dict]    = Field(default_factory=list)
    projects:           list[dict]    = Field(default_factory=list)


class DeleteResponse(BaseModel):
    message: str


# ── Conversion helpers ────────────────────────────────────────────────────────

def resume_to_detail(r) -> ResumeDetail:
    """Convert SQLAlchemy Resume row → ResumeDetail schema."""
    return ResumeDetail(
        id=r.id,
        filename=r.filename,
        file_size_kb=r.file_size_kb,
        uploaded_at=r.uploaded_at,
        parse_status=r.parse_status,
        personal=PersonalInfo(
            full_name=r.full_name,
            email=r.email,
            phone=r.phone,
            location=r.location,
            linkedin_url=r.linkedin_url,
            github_url=r.github_url,
            summary=r.summary,
        ),
        skills=r.skills or [],
        experience=[ExperienceItem(**e) for e in (r.experience or [])],
        education=[EducationItem(**e)   for e in (r.education  or [])],
        certifications=[CertificationItem(**c) for c in (r.certifications or [])],
        projects=[ProjectItem(**p)      for p in (r.projects   or [])],
        languages=r.languages    or [],
        achievements=r.achievements or [],
        interview_metadata=InterviewMetadata(
            experience_level=r.experience_level,
            suggested_roles=r.suggested_roles    or [],
            primary_tech_stack=r.primary_tech_stack or [],
            interview_topics=r.interview_topics  or [],
            strength_areas=r.strength_areas      or [],
            gap_areas=r.gap_areas                or [],
        ),
    )


def resume_to_summary(r) -> ResumeSummary:
    return ResumeSummary(
        id=r.id,
        filename=r.filename,
        full_name=r.full_name,
        email=r.email,
        experience_level=r.experience_level,
        skills_count=len(r.skills or []),
        uploaded_at=r.uploaded_at,
        parse_status=r.parse_status,
    )
