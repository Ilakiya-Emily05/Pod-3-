from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.assessment_status import AttemptStatus


class GrammarQuestionOptionBase(BaseModel):
    option_text: str = Field(min_length=1)
    sort_order: int = Field(ge=1)
    is_correct: bool = False


class GrammarQuestionOptionCreate(GrammarQuestionOptionBase):
    pass


class GrammarQuestionOptionUpdate(BaseModel):
    option_text: str | None = Field(default=None, min_length=1)
    sort_order: int | None = Field(default=None, ge=1)
    is_correct: bool | None = None


class GrammarQuestionOptionRead(GrammarQuestionOptionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GrammarQuestionBase(BaseModel):
    question_text: str = Field(min_length=1)
    sort_order: int = Field(ge=1)
    points: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.00"))


class GrammarQuestionCreate(GrammarQuestionBase):
    options: list[GrammarQuestionOptionCreate] = Field(default_factory=list)


class GrammarQuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=1)
    sort_order: int | None = Field(default=None, ge=1)
    points: Decimal | None = Field(default=None, ge=Decimal("0.00"))


class GrammarQuestionRead(GrammarQuestionBase):
    id: UUID
    assessment_id: UUID
    options: list[GrammarQuestionOptionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GrammarAssessmentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = None
    topic: str | None = Field(default=None, max_length=255)
    total_questions: int = Field(default=0, ge=0)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    is_active: bool = True


class GrammarAssessmentCreate(GrammarAssessmentBase):
    questions: list[GrammarQuestionCreate] = Field(default_factory=list)


class GrammarAssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = None
    topic: str | None = Field(default=None, max_length=255)
    total_questions: int | None = Field(default=None, ge=0)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class GrammarAssessmentRead(GrammarAssessmentBase):
    id: UUID
    questions: list[GrammarQuestionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GrammarAttemptAnswerCreate(BaseModel):
    question_id: UUID
    selected_option_id: UUID | None = None


class GrammarAttemptAnswerRead(BaseModel):
    id: UUID
    question_id: UUID
    selected_option_id: UUID | None
    is_correct: bool | None

    model_config = ConfigDict(from_attributes=True)


class GrammarAttemptBase(BaseModel):
    assessment_id: UUID
    user_id: UUID | None = None
    user_email: str | None = Field(default=None, max_length=320)


class GrammarAttemptCreate(GrammarAttemptBase):
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GrammarAttemptUpdate(BaseModel):
    status: AttemptStatus | None = None
    submitted_at: datetime | None = None
    answered_questions: int | None = Field(default=None, ge=0)
    correct_answers: int | None = Field(default=None, ge=0)
    score: Decimal | None = Field(default=None, ge=Decimal("0.00"))


class GrammarAttemptRead(BaseModel):
    id: UUID
    assessment_id: UUID
    user_id: UUID | None
    user_email: str | None
    status: AttemptStatus
    started_at: datetime
    submitted_at: datetime | None
    total_questions: int
    answered_questions: int
    correct_answers: int
    score: Decimal
    answers: list[GrammarAttemptAnswerRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
