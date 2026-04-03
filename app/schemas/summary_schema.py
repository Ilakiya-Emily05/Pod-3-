from typing import List

from pydantic import BaseModel


class TestSummaryResponse(BaseModel):
    session_id: int
    total_questions: int
    total_correct: int
    accuracy: float
    passed_subtopics: int
    failed_subtopics: int
    completed_subtopics: int
    weak_topics: List[str]
    strong_topics: List[str]
    status: str
