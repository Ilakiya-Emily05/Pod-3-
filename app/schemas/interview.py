from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.interview_system import DifficultyLevel


# ── Keyword / Skill Schemas ─────────────────────────────────────────────────

class KeywordIngest(BaseModel):
    """Payload sent by teammate's module to store keywords for a user."""
    user_id: str
    keywords: list[str]


class KeySkillOut(BaseModel):
    id: UUID
    user_id: str
    keyword: str

    model_config = {"from_attributes": True}


# ── Question Schemas ─────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id: UUID
    text: str
    difficulty: DifficultyLevel
    skill_id: UUID

    model_config = {"from_attributes": True}


class QuestionWithAnswer(BaseModel):
    id: UUID
    text: str
    answer_key: str
    difficulty: DifficultyLevel
    skill_id: UUID

    model_config = {"from_attributes": True}


# ── Practice Session Schemas ─────────────────────────────────────────────────

class SubmitPracticeAnswer(BaseModel):
    """User submits an answer in the AI Practice section (Section 1)."""
    question_id: UUID
    user_answer: str


class PracticeAnswerFeedback(BaseModel):
    """Immediate feedback returned to user in Section 1."""
    is_correct: bool
    feedback: str
    transcription: str | None = None
    confidence_score: int | None = None
    next_question: QuestionOut | None = None
    practice_complete: bool = False


class StartInterviewRequest(BaseModel):
    """Start a new mock interview session."""
    user_id: str


# ── Mock Session List / Result Schemas (for frontend) ────────────────────────

class MockSessionOut(BaseModel):
    """Summary of a single mock interview session."""
    session_id: UUID
    status: str
    created_at: datetime
    response_count: int

    model_config = {"from_attributes": True}


class UserResponseOut(BaseModel):
    """A single question-answer pair within a session result."""
    question_text: str
    user_answer: str
    confidence_score: int | None = None
    is_correct: bool | None = None
    feedback: str | None = None


class MockSessionResultOut(BaseModel):
    """Full result for a completed mock interview session."""
    session_id: UUID
    status: str
    gap_analysis: str | None = None
    responses: list[UserResponseOut]


class BatchSessionOut(BaseModel):
    """Output for a batch mock interview session (10 questions for 5 mins)."""
    session_id: UUID
    questions: list[QuestionOut]

