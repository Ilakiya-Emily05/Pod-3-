"""
Interview Helpers — shared utilities for interview services.
Pure functions and async DB helpers with no side effects.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)

logger = logging.getLogger(__name__)

FILLER_WORDS: list[str] = ["um", "uh", "like", "so", "you know", "actually", "erm"]


# ── Score helpers ─────────────────────────────────────────────────────────────


def performance_level(score: int | None) -> str:
    """Map numeric score to a human-readable performance label."""
    if score is None:
        return "N/A"
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Satisfactory"
    if score >= 40:
        return "Needs Improvement"
    return "Poor"


def next_difficulty(current: DifficultyLevel, is_correct: bool) -> DifficultyLevel:
    """Adaptive difficulty: correct → move up one level, wrong → stay."""
    ladder = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    idx = ladder.index(current)
    if is_correct and idx < len(ladder) - 1:
        return ladder[idx + 1]
    return current


# ── Serialization helpers ─────────────────────────────────────────────────────


def safe_dict(value: object) -> dict | None:
    """Return dict or None — never a string 'null'."""
    return value if isinstance(value, dict) else None


def safe_pronunciation(result: object) -> dict:
    """Ensure pronunciation result is always JSON-serializable."""
    empty: dict = {
        "phoneme_score": None,
        "fluency_score": None,
        "mistakes": [],
        "tips": [],
    }
    if not isinstance(result, dict):
        return empty
    return {
        "phoneme_score": result.get("phoneme_score")
        if isinstance(result.get("phoneme_score"), (int, float, type(None)))
        else None,
        "fluency_score": result.get("fluency_score")
        if isinstance(result.get("fluency_score"), (int, float, type(None)))
        else None,
        "mistakes": result.get("mistakes") if isinstance(result.get("mistakes"), list) else [],
        "tips": result.get("tips") if isinstance(result.get("tips"), list) else [],
    }


def question_to_dict(q: Question) -> dict:
    """Convert SQLAlchemy Question to a plain serializable dict."""
    return {
        "id": str(q.id),
        "text": q.text,
        "difficulty": q.difficulty,
        "skill_id": str(q.skill_id),
    }


def count_fillers(text: str) -> int:
    """Count filler words in a transcript."""
    lower = text.lower()
    return sum(lower.count(f) for f in FILLER_WORDS)


def parse_gap_analysis(gap: str) -> tuple[list[str], list[str]]:
    """
    Parse AI-generated gap analysis into strengths and improvements lists.

    Returns:
        Tuple of (strengths, improvements), each capped at 3 items.
    """
    strengths: list[str] = []
    improvements: list[str] = []
    current_section: str | None = None

    for line in gap.split("\n"):
        line = line.strip()
        if not line:
            continue
        line_upper = line.upper()

        if "STRENGTH" in line_upper:
            current_section = "strengths"
            continue
        if any(k in line_upper for k in ["WEAKNESS", "IMPROVEMENT", "RECOMMENDATION"]):
            current_section = "improvements"
            continue
        if ":**" in line or line.startswith("#"):
            continue

        is_bullet = line.startswith(("- ", "* ")) or (
            len(line) > 2 and line[0].isdigit() and line[1] in ".)"
        )
        if not is_bullet:
            continue

        clean = line.lstrip("0123456789.-*) ").replace("**", "").strip()
        if not clean or len(clean) < 5:
            continue

        if current_section == "strengths" and len(strengths) < 3:
            strengths.append(clean)
        elif current_section == "improvements" and len(improvements) < 3:
            improvements.append(clean)

    return strengths, improvements


# ── DB query helpers ──────────────────────────────────────────────────────────


async def fetch_question(
    db: AsyncSession,
    skill_id: UUID,
    difficulty: DifficultyLevel,
    exclude_ids: list[UUID],
) -> Question | None:
    """Fetch one unused question for a given skill and difficulty."""
    stmt = (
        select(Question)
        .where(
            Question.skill_id == skill_id,
            Question.difficulty == difficulty,
            Question.id.notin_(exclude_ids) if exclude_ids else True,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_skills_for_user(db: AsyncSession, user_id: str) -> list[KeySkill]:
    """Return all skills stored for the given user."""
    result = await db.execute(select(KeySkill).where(KeySkill.user_id == user_id))
    return list(result.scalars().all())


async def get_previous_completed_score(db: AsyncSession, user_id: str) -> int | None:
    """Fetch overall_score of the most recent completed session."""
    stmt = (
        select(InterviewSession.overall_score)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.overall_score.isnot(None),
            InterviewSession.deleted_at.is_(None),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_answered_ids(db: AsyncSession, session_id: UUID) -> list[UUID]:
    """Return all question IDs already answered in a session."""
    result = await db.execute(
        select(UserResponse.question_id).where(UserResponse.session_id == session_id)
    )
    return list(result.scalars().all())


async def get_response_count(db: AsyncSession, session_id: UUID) -> int:
    """Return count of responses saved for a session."""
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(UserResponse.id)).where(UserResponse.session_id == session_id)
    )
    return result.scalar_one()
