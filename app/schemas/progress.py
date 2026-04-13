from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID


class ProgressStart(BaseModel):
    user_id: UUID
    module_type: str
    module_id: UUID


class ProgressComplete(BaseModel):
    score: Decimal | None = None
    total_questions: int | None = None
    correct_answers: int | None = None


class ProgressResponse(BaseModel):
    id: UUID
    user_id: str
    module_type: str
    module_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    score: Decimal | None
    total_questions: int | None
    correct_answers: int | None
    created_at: datetime | None
    updated_at: datetime | None


class UserProgressSummary(BaseModel):
    total_modules_started: int
    total_modules_completed: int
    average_score: Decimal | None
    modules_by_type: dict[str, int]


__all__ = ["ProgressComplete", "ProgressResponse", "ProgressStart", "UserProgressSummary"]
