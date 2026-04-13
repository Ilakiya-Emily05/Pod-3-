from uuid import UUID

from pydantic import BaseModel


class ProgressRecordRequest(BaseModel):
    user_id: UUID
    module: str
    topic: str
    subtopic: str
    is_correct: bool
    time_spent_secs: int | None = 0


class ProgressRecordResponse(BaseModel):
    user_id: UUID
    module: str
    topic: str
    subtopic: str
    total_attempts: int
    correct_attempts: int
    accuracy_pct: float
    mastery_achieved: bool


class ModuleDetailItem(BaseModel):
    topic: str
    subtopic: str
    total_attempts: int
    correct_attempts: int
    accuracy_pct: float
    mastery_achieved: bool


class ModuleDetailsResponse(BaseModel):
    user_id: UUID
    module: str
    data: list[ModuleDetailItem]


class SummaryResponse(BaseModel):
    user_id: UUID
    modules: dict
    overall_completion_pct: float
    streak_days: int
