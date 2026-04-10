from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuestionBase(BaseModel):
    topic: str
    subtopic: str
    question_text: str
    options: dict[str, str]
    correct_answer: str


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(BaseModel):
    id: UUID
    topic: str
    subtopic: str
    question_text: str
    options: dict[str, str]

    model_config = ConfigDict(from_attributes=True)
