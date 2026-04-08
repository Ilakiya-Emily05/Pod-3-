"""
Interview Progress Service — improvement tracking, milestones, consistency.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import desc

from app.models.analytics_models import SkillScoreHistory, UserMilestone
from app.models.interview_system import (
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)
from app.services.interview_helpers import (
    count_fillers,
    parse_gap_analysis,
    performance_level,
)

logger = logging.getLogger(__name__)

_SORT_MAP = {
    "date_desc": InterviewSession.created_at.desc(),
    "date_asc": InterviewSession.created_at.asc(),
    "score_desc": InterviewSession.overall_score.desc(),
    "score_asc": InterviewSession.overall_score.asc(),
}


# ── History ───────────────────────────────────────────────────────────────────


async def get_user_sessions(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    interview_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "date_desc",
) -> dict:
    """Return paginated session history with summary block."""
    base_query = select(InterviewSession).where(
        InterviewSession.user_id == user_id,
        InterviewSession.deleted_at.is_(None),
    )
    if interview_type:
        base_query = base_query.where(InterviewSession.interview_type == interview_type)
    if date_from:
        base_query = base_query.where(InterviewSession.created_at >= date_from)
    if date_to:
        base_query = base_query.where(InterviewSession.created_at <= date_to)
    base_query = base_query.order_by(_SORT_MAP.get(sort, InterviewSession.created_at.desc()))

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(base_query.offset(offset).limit(limit))
    sessions = result.scalars().all()

    session_list = [await _build_session_summary(db, s) for s in sessions]
    summary = await _build_summary(db, user_id, session_list)

    return {
    "total": total,
    "page": page,
    "limit": limit,
    "sessions": session_list,
    "summary": summary,
}


async def _build_session_summary(db: AsyncSession, s: InterviewSession) -> dict:
    q_count = (await db.execute(
        select(func.count(UserResponse.id)).where(UserResponse.session_id == s.id)
    )).scalar_one()
    has_recordings = (await db.execute(
        select(func.count(UserResponse.id)).where(
            UserResponse.session_id == s.id, UserResponse.audio_url.isnot(None)
        )
    )).scalar_one() > 0
    key_skills = list((await db.execute(
        select(KeySkill.keyword)
        .join(Question, Question.skill_id == KeySkill.id)
        .join(UserResponse, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == s.id).distinct()
    )).scalars().all())

    return {
        "session_id": s.id, "interview_type": s.interview_type, "status": s.status,
        "date": s.created_at, "started_at": s.started_at, "ended_at": s.ended_at,
        "duration_mins": s.duration_mins, "questions_count": q_count,
        "overall_score": s.overall_score, "performance_level": performance_level(s.overall_score),
        "improvement_delta": s.improvement_delta, "has_recordings": has_recordings,
        "has_report": s.feedback is not None and s.status == "completed",
        "key_skills_tested": key_skills,
    }


async def _build_summary(db: AsyncSession, user_id: str, session_list: list[dict]) -> dict:
    scores = [
    s["overall_score"]
    for s in session_list
    if s["overall_score"] is not None and s["status"] == "completed"
]
    last5 = list((await db.execute(
        select(InterviewSession.overall_score).where(
            InterviewSession.user_id == user_id, InterviewSession.status == "completed",
            InterviewSession.overall_score.isnot(None), InterviewSession.deleted_at.is_(None),
        ).order_by(InterviewSession.created_at.desc()).limit(5)
    )).scalars().all())
    trend = None
    if len(last5) >= 2:
        delta = last5[0] - last5[-1]
        trend = f"{'+' if delta >= 0 else ''}{delta}% over last {len(last5)} interviews"
    top = (await db.execute(
        select(InterviewSession.interview_type, func.count(InterviewSession.id).label("cnt"))
        .where(InterviewSession.user_id == user_id, InterviewSession.deleted_at.is_(None))
        .group_by(InterviewSession.interview_type).order_by(desc("cnt")).limit(1)
    )).first()
    return {
        "total_interviews": len(session_list),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "improvement_trend": trend,
        "most_practiced_type": top[0] if top else None,
        "total_time_mins": sum(s["duration_mins"] or 0 for s in session_list),
    }


# ── Replay ────────────────────────────────────────────────────────────────────


async def get_session_result(db: AsyncSession, session_id: UUID) -> dict:
    """Return full replay data for a completed session."""
    session = (await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session is still active.")

    rows = (await db.execute(
        select(UserResponse, Question)
        .join(Question, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == session_id)
        .order_by(UserResponse.question_index.asc().nullslast(), UserResponse.created_at.asc())
    )).all()

    questions = [await _build_question_detail(db, i, row) for i, row in enumerate(rows)]
    strengths, improvements = parse_gap_analysis(session.feedback or "")

    return {
        "session_id": str(session.id), "user_id": session.user_id,
        "interview_type": session.interview_type, "status": session.status,
        "started_at": session.started_at, "ended_at": session.ended_at,
        "duration_mins": session.duration_mins, "overall_score": session.overall_score,
        "improvement_delta": session.improvement_delta, "gap_analysis": session.feedback,
        "questions": questions,
        "report_summary": {"strengths": strengths, "improvements": improvements},
    }


async def _build_question_detail(db: AsyncSession, index: int, row: object) -> dict:
    ur, q = row.UserResponse, row.Question
    skill_keyword = (await db.execute(
        select(KeySkill.keyword).where(KeySkill.id == q.skill_id)
    )).scalar_one_or_none()
    p_data = ur.pronunciation_data or {}
    mistakes = p_data.get("mistakes", []) if isinstance(p_data.get("mistakes"), list) else []
    mispronounced = [
        m.get("expected", "") for m in mistakes
        if isinstance(m, dict) and m.get("type") in ("wrong", "missing") and m.get("expected")
    ]
    return {
        "question_id": str(q.id), "question_number": index + 1,
        "question_text": q.text, "difficulty": q.difficulty,
        "skill_tags": [skill_keyword] if skill_keyword else [],
        "response": {
            "user_answer": ur.user_answer,
            "response_time_secs": ur.time_taken_sec,
            "audio_url": ur.audio_url,
            },
        "evaluation": {
            "score": ur.confidence_score,
            "is_correct": ur.is_correct,
            "feedback": ur.feedback,
            "model_answer": q.answer_key,
            },
        "pronunciation": {
            "score": ur.pronunciation_score, "mispronounced_words": mispronounced,
            "filler_count": count_fillers(ur.user_answer or ""),
            "tips": p_data.get("tips", []) if isinstance(p_data.get("tips"), list) else [],
            "fluency_score": p_data.get("fluency_score"),
        },
    }


# ── Progress ──────────────────────────────────────────────────────────────────


async def get_improvement_history(db: AsyncSession, user_id: str) -> dict:
    """Return score progression, skill improvement, consistency, and milestones."""
    sessions = (await db.execute(
        select(InterviewSession).where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.deleted_at.is_(None),
        ).order_by(InterviewSession.created_at.asc())
    )).scalars().all()

    scores = [s.overall_score for s in sessions if s.overall_score is not None]
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return {
        "user_id": user_id,
        "total_interviews": len(sessions),
        "interviews_this_month": sum(1 for s in sessions if s.created_at >= month_start),
        "score_progression": [
            {
                "date": s.created_at.strftime("%Y-%m-%d"),
                "score": s.overall_score,
                "type": s.interview_type,
                }
            for s in sessions if s.overall_score is not None
        ],
        "skill_improvement": await _build_skill_improvement(db, user_id),
        "consistency": _build_consistency(sessions, now),
        "milestones": await _build_milestones(db, user_id),
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "best_score": max(scores) if scores else None,
    }


async def _build_skill_improvement(db: AsyncSession, user_id: str) -> list[dict]:
    rows = (await db.execute(
        select(SkillScoreHistory).where(SkillScoreHistory.user_id == user_id)
        .order_by(SkillScoreHistory.recorded_at.asc())
    )).scalars().all()
    skill_map: dict[str, list[int]] = {}
    for row in rows:
        if row.skill_name and row.score is not None:
            skill_map.setdefault(row.skill_name, []).append(row.score)
    return [
        {"skill": skill, "initial_score": sl[0], "current_score": sl[-1],
         "change": f"+{sl[-1] - sl[0]}" if sl[-1] >= sl[0] else str(sl[-1] - sl[0])}
        for skill, sl in skill_map.items()
    ]


def _build_consistency(sessions: list[InterviewSession], now: datetime) -> dict:
    streak = longest_gap = total_weeks = 0
    if sessions:
        prev_date = now.date()
        for s in reversed(sessions):
            s_date = s.created_at.date()
            if (prev_date - s_date).days <= 1:
                streak += 1
                prev_date = s_date
            else:
                break
        dates = [s.created_at for s in sessions]
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i - 1]).days
            if gap > longest_gap:
                longest_gap = gap
        if len(sessions) >= 2:
            total_days = (sessions[-1].created_at - sessions[0].created_at).days or 1
            total_weeks = max(1, total_days / 7)
    avg_per_week = round(len(sessions) / total_weeks, 1) if total_weeks > 0 else len(sessions)
    return {
    "avg_interviews_per_week": avg_per_week,
    "longest_gap_days": longest_gap,
    "current_streak": streak,
}


async def _build_milestones(db: AsyncSession, user_id: str) -> list[dict]:
    rows = (await db.execute(
        select(UserMilestone).where(UserMilestone.user_id == user_id)
        .order_by(UserMilestone.achieved_at.asc())
    )).scalars().all()
    return [
    {
        "name": m.milestone_name,
        "achieved_at": m.achieved_at.strftime("%Y-%m-%d"),
    }
    for m in rows
]
