from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class ProgressRecordRequest(BaseModel):
    user_id: UUID
    module: str
    topic: str
    subtopic: str
    is_correct: bool
    time_spent_secs: Optional[int] = 0


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
    data: List[ModuleDetailItem]


class SummaryResponse(BaseModel):
    user_id: UUID
    modules: dict
    overall_completion_pct: float
    streak_days: int
