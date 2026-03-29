from typing import Dict

from pydantic import BaseModel, ConfigDict


class QuestionBase(BaseModel):
    topic: str
    subtopic: str
    question_text: str
    options: Dict[str, str]
    correct_answer: str


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(BaseModel):
    id: int
    topic: str
    subtopic: str
    question_text: str
    options: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)
