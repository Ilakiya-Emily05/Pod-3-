from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.assessment_status import AttemptStatus, CEFRLevel
from app.utils.validators import validate_cefr_result_level


class ListeningQuestionOptionBase(BaseModel):
    option_text: str = Field(min_length=1)
    sort_order: int = Field(ge=1)
    is_correct: bool = False


class ListeningQuestionOptionCreate(ListeningQuestionOptionBase):
    pass


class ListeningQuestionOptionUpdate(BaseModel):
    option_text: str | None = Field(default=None, min_length=1)
    sort_order: int | None = Field(default=None, ge=1)
    is_correct: bool | None = None


class ListeningQuestionOptionRead(BaseModel):
    id: UUID
    option_text: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListeningQuestionBase(BaseModel):
    question_text: str = Field(min_length=1)
    sort_order: int = Field(ge=1)
    points: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.00"))
    cefr_level: CEFRLevel
    difficulty_score: Decimal = Field(ge=Decimal("0.00"))


class ListeningQuestionCreate(ListeningQuestionBase):
    options: list[ListeningQuestionOptionCreate] = Field(default_factory=list)


class ListeningQuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=1)
    sort_order: int | None = Field(default=None, ge=1)
    points: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    cefr_level: CEFRLevel | None = None
    difficulty_score: Decimal | None = Field(default=None, ge=Decimal("0.00"))


class ListeningQuestionRead(ListeningQuestionBase):
    id: UUID
    assessment_id: UUID
    cefr_level: CEFRLevel | None = None
    difficulty_score: Decimal | None = None
    options: list[ListeningQuestionOptionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListeningAssessmentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    audio_url: str = Field(min_length=1, max_length=1024)
    audio_duration_seconds: int | None = Field(default=None, ge=1)
    total_questions: int = Field(default=0, ge=0)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    is_active: bool = True


class ListeningAssessmentCreate(ListeningAssessmentBase):
    questions: list[ListeningQuestionCreate] = Field(default_factory=list)


class ListeningAssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    audio_url: str | None = Field(default=None, min_length=1, max_length=1024)
    audio_duration_seconds: int | None = Field(default=None, ge=1)
    total_questions: int | None = Field(default=None, ge=0)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class ListeningAssessmentRead(ListeningAssessmentBase):
    id: UUID
    questions: list[ListeningQuestionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListeningAttemptAnswerCreate(BaseModel):
    question_id: UUID
    selected_option_id: UUID | None = None


class ListeningAttemptAnswerRead(BaseModel):
    id: UUID
    question_id: UUID
    selected_option_id: UUID | None
    cefr_level: CEFRLevel | None
    difficulty_score: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class ListeningAttemptBase(BaseModel):
    assessment_id: UUID
    user_id: UUID | None = None
    user_email: str | None = Field(default=None, max_length=320)


class ListeningAttemptCreate(ListeningAttemptBase):
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ListeningAttemptUpdate(BaseModel):
    status: AttemptStatus | None = None
    submitted_at: datetime | None = None
    answered_questions: int | None = Field(default=None, ge=0)
    correct_answers: int | None = Field(default=None, ge=0)
    ability_score: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        le=Decimal("1.00"),
    )
    cefr_level: str | None = Field(default=None, min_length=2, max_length=3)

    @field_validator("cefr_level", mode="before")
    @classmethod
    def validate_cefr_level(cls, value: str | None) -> str | None:
        return validate_cefr_result_level(value)


class ListeningAttemptRead(BaseModel):
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
    ability_score: Decimal | None
    cefr_level: str | None
    answers: list[ListeningAttemptAnswerRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_validator("cefr_level", mode="before")
    @classmethod
    def validate_cefr_level(cls, value: str | None) -> str | None:
        return validate_cefr_result_level(value)

    model_config = ConfigDict(from_attributes=True)
