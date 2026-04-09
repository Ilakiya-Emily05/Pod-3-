from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel


class ProgressStart(BaseModel):
    user_id: UUID
    module_type: str
    module_id: UUID


class ProgressComplete(BaseModel):
    score: Optional[Decimal] = None
    total_questions: Optional[int] = None
    correct_answers: Optional[int] = None


class ProgressResponse(BaseModel):
    id: UUID
    user_id: str
    module_type: str
    module_id: UUID
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    score: Optional[Decimal]
    total_questions: Optional[int]
    correct_answers: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserProgressSummary(BaseModel):
    total_modules_started: int
    total_modules_completed: int
    average_score: Optional[Decimal]
    modules_by_type: Dict[str, int]


__all__ = ["ProgressStart", "ProgressComplete", "ProgressResponse", "UserProgressSummary"]
