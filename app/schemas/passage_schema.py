from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PassageStartResponse(BaseModel):
    session_id: UUID
    status: str


class PassageResponse(BaseModel):
    session_id: UUID
    passage: str


class PassageQuestion(BaseModel):
    id: UUID
    question_text: str
    options: dict[str, str]


class PassageQuestionsResponse(BaseModel):
    session_id: UUID
    questions: list[PassageQuestion]


class PassageAnswerRequest(BaseModel):
    session_id: UUID
    question_id: UUID
    selected_answer: str


class PassageAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str


class PassageSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    total_questions: int
    total_correct: int
    accuracy: float
    status: str
    weak_areas: list[str]
    strong_areas: list[str]
