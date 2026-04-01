from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressStart(BaseModel):
    """Schema for starting a module."""

    user_id: UUID = Field(..., description="User ID")
    module_type: str = Field(..., description="Module type: reading, listening, or grammar")
    module_id: UUID = Field(..., description="Module/Assessment ID")


class ProgressComplete(BaseModel):
    """Schema for completing a module."""

    score: Decimal = Field(..., ge=0, description="Score achieved")
    total_questions: int = Field(..., ge=1, description="Total questions in module")
    correct_answers: int = Field(..., ge=0, description="Number of correct answers")


class ProgressResponse(BaseModel):
    """Schema for progress response."""

    id: UUID
    user_id: UUID
    module_type: str
    module_id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    score: Decimal | None
    total_questions: int | None
    correct_answers: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProgressSummary(BaseModel):
    """Summary of user progress across all modules."""

    total_modules_started: int
    total_modules_completed: int
    total_score: Decimal
    average_score: Decimal
    modules_by_type: dict[str, int]  # module_type -> count
