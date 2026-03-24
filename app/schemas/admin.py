from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
class AdminSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)

    @property
    def passwords_match(self) -> bool:
        return self.password == self.confirm_password


class AdminAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_email: EmailStr


class UserResponse(BaseModel):
    """User information response."""

    id: UUID
    email: str
    is_active: bool
    profile_completed: bool
    created_at: datetime
    profile: dict | None = None

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    """Paginated list of users."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnalyticsSummary(BaseModel):
    """Platform analytics summary."""

    total_users: int
    active_users: int
    total_assessments_created: int
    total_attempts: int
    average_user_score: Decimal
    cefr_distribution: dict[str, int]  # CEFR level -> count
    module_completion_rate: float  # percentage
    recent_activity: dict[str, int]  # last 7 days activity


class QuestionCreate(BaseModel):
    """Schema for creating a question (admin)."""

    assessment_type: str = Field(..., description="Type: reading, listening, grammar")
    assessment_id: UUID = Field(..., description="Assessment ID")
    question_text: str = Field(..., min_length=1, max_length=2000)
    sort_order: int = Field(..., ge=1)
    points: Decimal = Field(..., ge=0)
    options: list[dict] = Field(..., description="List of options with is_correct flag")
