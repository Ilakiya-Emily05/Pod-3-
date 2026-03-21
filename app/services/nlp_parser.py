import logging
from typing import Optional
from pydantic import BaseModel, Field
from app.prompts.resume_parser import (
    RESUME_PARSER_SYSTEM_PROMPT,
    get_resume_user_prompt,
)
from app.config.settings import settings

log = logging.getLogger(__name__)


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


class ProjectItem(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    tech_stack:  list[str]     = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None


class ResumeStructuredOutput(BaseModel):
    full_name:    Optional[str] = None
    email:        Optional[str] = None
    phone:        Optional[str] = None
    location:     Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url:   Optional[str] = None
    summary:      Optional[str] = None

    skills:         list[str]               = Field(default_factory=list)
    experience:     list[ExperienceItem]    = Field(default_factory=list)
    education:      list[EducationItem]     = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects:       list[ProjectItem]       = Field(default_factory=list)
    languages:      list[str]               = Field(default_factory=list)
    achievements:   list[str]               = Field(default_factory=list)

    experience_level:   Optional[str] = None
    suggested_roles:    list[str]     = Field(default_factory=list)
    primary_tech_stack: list[str]     = Field(default_factory=list)
    interview_topics:   list[str]     = Field(default_factory=list)
    strength_areas:     list[str]     = Field(default_factory=list)
    gap_areas:          list[str]     = Field(default_factory=list)


def parse_resume(raw_text: str) -> dict:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment or .env file.")
    return _call_openai(raw_text, api_key)


def _call_openai(raw_text: str, api_key: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    log.info("Calling OpenAI gpt-4o-mini with Structured Outputs...")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": RESUME_PARSER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": get_resume_user_prompt(raw_text),
            },
        ],
        response_format=ResumeStructuredOutput,
    )

    parsed = response.choices[0].message.parsed

    return {
        "full_name":          parsed.full_name,
        "email":              parsed.email,
        "phone":              parsed.phone,
        "location":           parsed.location,
        "linkedin_url":       parsed.linkedin_url,
        "github_url":         parsed.github_url,
        "summary":            parsed.summary,
        "skills":             parsed.skills,
        "experience":         [e.model_dump() for e in parsed.experience],
        "education":          [e.model_dump() for e in parsed.education],
        "certifications":     [c.model_dump() for c in parsed.certifications],
        "projects":           [p.model_dump() for p in parsed.projects],
        "languages":          parsed.languages,
        "achievements":       parsed.achievements,
        "experience_level":   parsed.experience_level,
        "suggested_roles":    parsed.suggested_roles,
        "primary_tech_stack": parsed.primary_tech_stack,
        "interview_topics":   parsed.interview_topics,
        "strength_areas":     parsed.strength_areas,
        "gap_areas":          parsed.gap_areas,
    }
