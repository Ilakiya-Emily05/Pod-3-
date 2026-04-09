from datetime import datetime
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


class SingleAnswer(BaseModel):
    attempt_id: UUID
    question_id: UUID
    option_key: str  # A,B,C,D


class AnswerRequest(BaseModel):
    attempt_id: UUID
    answers: list[SingleAnswer]  # SingleAnswer also has attempt_id


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    attempt_id: UUID
    status: str
    hexaco_scores: dict[str, float]
    weak_traits: list[str]
    strong_traits: list[str]
    needs_adaptive_test: bool


class ModuleRecommendation(BaseModel):
    module: str
    reason: str
    priority: str


class BehavioralCompleteRequest(BaseModel):
    user_id: UUID
    session_id: UUID


class BehavioralCompleteResponse(BaseModel):
    user_id: UUID
    hexaco_profile: dict[str, float]
    personality_summary: str
    recommended_modules: list[ModuleRecommendation]
    learning_path_updated: bool


class TraitScore(BaseModel):
    score: float
    level: str


class BehavioralProfileResponse(BaseModel):
    user_id: UUID
    completed_at: datetime
    hexaco_scores: dict[str, TraitScore]
    strengths: list[str]
    development_areas: list[str]
    ai_personality_report: str
    needs_adaptive_test: bool
