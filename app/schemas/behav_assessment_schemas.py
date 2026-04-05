from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    option_key: str
    option_text: str


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    question_text: str
    options: dict[str, str]  # A,B,C,D → option text


class AssessmentSessionResponse(BaseModel):
    attempt_id: UUID
    questions: list[QuestionResponse]


class AnswerRequest(BaseModel):
    attempt_id: UUID
    question_id: UUID
    option_key: str  # A,B,C,D


class BulkAnswerRequest(BaseModel):
    attempt_id: UUID
    answers: list[AnswerRequest]  # Nested AnswerRequests also have attempt_id (optional redundant)


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    attempt_id: UUID
    status: str
    hexaco_scores: dict[str, float]
    weak_traits: list[str]
    strong_traits: list[str]
    comparative_low_traits: list[str]
    recommendation: str
    ai_analysis: dict[str, str]
    needs_adaptive_test: bool
