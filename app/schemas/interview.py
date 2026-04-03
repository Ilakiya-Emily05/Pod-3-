from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


# ── Enums ─────────────────────────────────────────────────────────
class DifficultyLevel(str):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ── Keyword / Skill Schemas ───────────────────────────────────────
class KeywordIngest(BaseModel):
    user_id: str
    keywords: list[str]


class KeySkillOut(BaseModel):
    id: UUID
    user_id: str
    keyword: str
    model_config = {"from_attributes": True}


# ── Question Schemas ──────────────────────────────────────────────
class QuestionOut(BaseModel):
    id: UUID
    text: str
    difficulty: str
    skill_id: UUID
    model_config = {"from_attributes": True}


class QuestionWithAnswer(BaseModel):
    id: UUID
    text: str
    answer_key: str
    difficulty: str
    skill_id: UUID
    model_config = {"from_attributes": True}


# ── Practice Schemas ──────────────────────────────────────────────
class SubmitPracticeAnswer(BaseModel):
    question_id: UUID
    user_answer: str


class PracticeAnswerFeedback(BaseModel):
    is_correct: bool
    feedback: str
    transcription: Optional[str] = None
    confidence_score: Optional[float] = None
    next_question: Optional[QuestionOut] = None
    practice_complete: bool = False


# ── Interview Session Schemas ─────────────────────────────────────
class StartInterviewRequest(BaseModel):
    user_id: str


class InterviewSessionOut(BaseModel):
    session_id: UUID
    status: str
    current_question: QuestionOut


class InterviewAnswerResponse(BaseModel):
    session_complete: bool
    next_question: Optional[QuestionOut] = None
    transcription: Optional[str] = None
    confidence_score: Optional[float] = None


class GapAnalysisFeedback(BaseModel):
    session_id: UUID
    feedback: str


# ── History / Replay Schemas ──────────────────────────────────────
class MockSessionOut(BaseModel):
    session_id: UUID
    status: str
    interview_type: Optional[str] = None
    date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_mins: Optional[int] = None
    response_count: int = 0
    overall_score: Optional[int] = None
    improvement_delta: Optional[float] = None
    has_recordings: bool = False
    model_config = {"from_attributes": True}


class UserResponseOut(BaseModel):
    question_index: Optional[int] = None
    question_text: str
    user_answer: str
    confidence_score: Optional[float] = None
    is_correct: Optional[bool] = None
    feedback: Optional[str] = None
    answered_at: Optional[datetime] = None
    time_taken_sec: Optional[int] = None
    audio_url: Optional[str] = None


class MockSessionResultOut(BaseModel):
    session_id: UUID
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_mins: Optional[int] = None
    overall_score: Optional[int] = None
    improvement_delta: Optional[float] = None
    gap_analysis: Optional[str] = None
    responses: list[UserResponseOut]


# ── Progress / Improvement Schemas ───────────────────────────────
class SessionScorePoint(BaseModel):
    session_id: UUID
    date: Optional[datetime] = None
    overall_score: Optional[int] = None
    improvement_delta: Optional[float] = None
    duration_mins: Optional[int] = None
    interview_type: Optional[str] = None


class ImprovementHistoryOut(BaseModel):
    user_id: str
    total_sessions: int
    average_score: Optional[float] = None
    best_score: Optional[int] = None
    sessions: list[SessionScorePoint]


# ── Batch Session ─────────────────────────────────────────────────
class BatchSessionOut(BaseModel):
    session_id: UUID
    questions: list[QuestionOut]