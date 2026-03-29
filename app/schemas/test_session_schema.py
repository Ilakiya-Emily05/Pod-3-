from pydantic import BaseModel, ConfigDict


class TestSessionResponse(BaseModel):
    session_id: int
    current_topic: str
    current_subtopic: str
    status: str
    total_questions_attended: int
    total_correct_answers: int

    model_config = ConfigDict(from_attributes=True)


class AnswerRequest(BaseModel):
    session_id: int
    question_id: int
    selected_answer: str


class AnswerResponse(BaseModel):
    is_correct: bool
    current_topic: str
    current_subtopic: str
    status: str
    total_questions_attended: int
    total_correct_answers: int
