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
    options: list[str]
    difficulty: DifficultyLevel
    skill_id: UUID

    model_config = {"from_attributes": True}


class QuestionWithAnswer(BaseModel):
    id: UUID
    text: str
    options: list[str]
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
    next_question: QuestionOut | None = None
    practice_complete: bool = False


# ── Mock Interview Schemas ────────────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    """Start a new mock interview session."""
    user_id: str


class InterviewSessionOut(BaseModel):
    session_id: UUID
    status: str
    current_question: QuestionOut


class SubmitInterviewAnswer(BaseModel):
    """User submits an answer during mock interview (Section 2)."""
    user_answer: str | None = None


class InterviewAnswerResponse(BaseModel):
    """Response after submitting an interview answer — no performance feedback shown."""
    session_complete: bool
    next_question: QuestionOut | None = None  # None when session is complete
    transcription: str | None = None
    confidence_score: float | None = None


class GapAnalysisFeedback(BaseModel):
    """Final Gap Analysis report shown at the end of the Mock Interview."""
    session_id: UUID
    feedback: str
