from pydantic import BaseModel, ConfigDict


class UserAnswerCreate(BaseModel):
    question_id: int
    selected_answer: str


class UserAnswerResponse(BaseModel):
    question_id: int
    selected_answer: str
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)
