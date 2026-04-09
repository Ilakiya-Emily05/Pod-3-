from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PhonemeStat(BaseModel):
    phoneme: str
    accuracy: float
    total_attempts: int
    correct_attempts: int
    last_attempted_at: datetime | None = None


class WeakPhoneme(BaseModel):
    phoneme: str
    error_rate: float = Field(..., ge=0.0, le=1.0)
    example_word: str | None = None


class StrongPhoneme(BaseModel):
    phoneme: str
    accuracy: float = Field(..., ge=0.0, le=1.0)


class LevelProgress(BaseModel):
    current: str
    exercises_at_level: int
    required_for_next: int
    avg_score_at_level: float


class UserPronunciationProfileOut(BaseModel):
    user_id: UUID  # int → UUID
    current_level: str
    overall_score_avg: float
    exercises_completed: int
    time_spent_total_mins: float
    weak_phonemes: list[WeakPhoneme]
    strong_phonemes: list[StrongPhoneme]
    level_progress: LevelProgress
    last_practice: datetime | None = None

    model_config = {"from_attributes": True}


class PhonemeDetailOut(BaseModel):
    phoneme: str
    total_attempts: int
    correct_attempts: int
    accuracy: float


class MistakeOut(BaseModel):
    expected: str
    spoken: str
    type: str  # "missing" | "wrong" | "extra"


class AnalyzeAudioOut(BaseModel):
    request_id: UUID  # str → UUID
    user_id: UUID  # int → UUID
    reference_text: str
    transcript: str
    ref_ipa: str
    user_ipa: str
    phoneme_score: float
    fluency_score: float
    overall_score: float
    weak_phonemes: list[WeakPhoneme]
    strong_phonemes: list[StrongPhoneme]
    mistakes: list[MistakeOut]
    tips: list[str]


class RecommendationSentence(BaseModel):
    sentence: str
    difficulty: str


class RecommendationItem(BaseModel):
    phoneme: str
    exercises: list[RecommendationSentence]


class PronunciationRecommendationOut(BaseModel):
    focus_areas: list[RecommendationItem]
    suggested_practice_time_mins: int
    next_milestone: str


class ListeningModuleOut(BaseModel):
    session_id: UUID  # str → UUID
    passage: str
    audio_url: str
    listening_questions: list[dict]


class ListeningEvalOut(BaseModel):
    session_id: UUID  # str → UUID
    expected_answer: str
    user_transcript: str
    relevance: float
    correctness: float
    feedback: str


class QuestionOut(BaseModel):
    difficulty: str
    question_text: str
