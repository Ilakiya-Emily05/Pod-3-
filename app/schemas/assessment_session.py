from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.assessment_session import (
    AssessmentSection,
    AssessmentSessionStatus,
    AssessmentSessionType,
)


class AssessmentSessionCreate(BaseModel):
    session_type: AssessmentSessionType


class AssessmentSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    session_type: AssessmentSessionType
    status: AssessmentSessionStatus
    current_section: AssessmentSection
    composite_cefr_result: str | None
    started_at: datetime
    completed_at: datetime | None


class AssessmentSessionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    session_type: AssessmentSessionType
    status: AssessmentSessionStatus
    current_section: AssessmentSection
    composite_cefr_result: str | None
    started_at: datetime
    completed_at: datetime | None
    section_scores: dict[str, float | int | str | None] = Field(default_factory=dict)