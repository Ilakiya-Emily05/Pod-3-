from pydantic import BaseModel, ConfigDict


class PassageStartResponse(BaseModel):
    session_id: int
    status: str


class PassageResponse(BaseModel):
    session_id: int
    passage: str


class PassageQuestion(BaseModel):
    id: int
    question_text: str
    options: dict[str, str]


class PassageQuestionsResponse(BaseModel):
    session_id: int
    questions: list[PassageQuestion]


class PassageAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    selected_answer: str


class PassageAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str


class PassageSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    total_questions: int
    total_correct: int
    accuracy: float
    status: str
    weak_areas: list[str]
    strong_areas: list[str]
