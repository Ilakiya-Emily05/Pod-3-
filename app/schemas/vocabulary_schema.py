from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class WordItem(BaseModel):
    word_id: UUID
    word: str
    definition: str
    cefr_level: Optional[str] = None
    example_sentence: Optional[str] = None

    # user progress
    last_reviewed_at: Optional[datetime] = None
    retention_score: Optional[float] = None
    next_review_due: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WordsResponse(BaseModel):
    session_id: UUID
    words: List[WordItem]
    total_words_in_session: int


class ResponseRecord(BaseModel):
    session_id: UUID
    user_id: UUID
    word_id: UUID

    # 👇 user-friendly input
    response: str  # "again", "hard", "medium", "easy"

    # ⏱️ optional (not used now)
    # response_time_ms: Optional[int] = None

class ResponseResult(BaseModel):
    word_id: UUID
    new_retention_score: float
    next_review_date: Optional[datetime]
    interval_days: int
    feedback: str

class VocabularyStats(BaseModel):
    total_words_learned: int
    words_mastered: int
    words_learning: int
    words_struggling: int