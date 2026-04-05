from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class WordItem(BaseModel):
    word_id: UUID
    word: str
    definition: str
    part_of_speech: Optional[str] = None
    industry: Optional[str] = None
    difficulty: Optional[str] = None
    example_sentence: Optional[str] = None
    pronunciation_audio_url: Optional[str] = None
    last_reviewed: Optional[datetime] = None
    retention_score: Optional[float] = None
    next_review_due: Optional[datetime] = None


class WordsResponse(BaseModel):
    session_id: UUID
    words: List[WordItem]
    total_words_in_session: int


class ResponseRecord(BaseModel):
    user_id: UUID
    word_id: UUID
    response_quality: int  # 0-5
    response_time_ms: int


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
    by_industry: dict
    streak_days: int
    words_due_today: int


class VocabularyListItem(BaseModel):
    list_id: UUID
    name: str
    industry: Optional[str]
    difficulty: Optional[str]
    word_count: Optional[int]
    description: Optional[str]


class StartListResult(BaseModel):
    list_id: UUID
    started: bool


__all__ = [
    "WordItem",
    "WordsResponse",
    "ResponseRecord",
    "ResponseResult",
    "VocabularyStats",
    "VocabularyListItem",
    "StartListResult",
]
