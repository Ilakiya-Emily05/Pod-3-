"""
Session Analytics Service — Sprint 2 Task 1

Updates aggregated stats, checks milestones, and records skill scores
after each completed interview session.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import desc

from app.models.analytics_models import SessionAnalytics, SkillScoreHistory, UserMilestone
from app.models.interview_system import InterviewSession, KeySkill

logger = logging.getLogger(__name__)

MILESTONES: list[tuple[str, str, object]] = [
    ("first_interview", "First Interview", lambda s, c: c == 1),
    ("score_70", "Score Above 70", lambda s, c: (s.overall_score or 0) >= 70),
    ("score_80", "Score Above 80", lambda s, c: (s.overall_score or 0) >= 80),
    ("score_90", "Score Above 90", lambda s, c: (s.overall_score or 0) >= 90),
    ("5_interviews", "5 Interviews Completed", lambda s, c: c >= 5),
    ("10_interviews", "10 Interviews Completed", lambda s, c: c >= 10),
    ("25_interviews", "25 Interviews Completed", lambda s, c: c >= 25),
]


class SessionAnalyticsService:
    """Manages aggregated session stats, milestones, and skill score history."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(self, user_id: str) -> SessionAnalytics:
        """Fetch existing analytics record or create a new one."""
        result = await self.db.execute(
            select(SessionAnalytics).where(SessionAnalytics.user_id == user_id)
        )
        analytics = result.scalar_one_or_none()
        if not analytics:
            analytics = SessionAnalytics(user_id=user_id)
            self.db.add(analytics)
            await self.db.flush()
        return analytics

    async def update(self, user_id: str, session: InterviewSession) -> None:
        """Update aggregated stats after a completed session."""
        analytics = await self.get_or_create(user_id)
        analytics.total_sessions += 1
        analytics.total_time_mins += session.duration_mins or 0
        analytics.last_session_at = session.ended_at

        if session.overall_score is not None:
            self._update_score_stats(analytics, session.overall_score)

        top_type = await self._get_most_practiced_type(user_id)
        if top_type:
            analytics.most_practiced_type = top_type

        analytics.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.check_milestones(user_id, session, analytics.total_sessions)

    def _update_score_stats(self, analytics: SessionAnalytics, score: int) -> None:
        """Recalculate avg, best, worst scores in-place."""
        if analytics.avg_score is None:
            analytics.avg_score = score
        else:
            total = float(analytics.avg_score) * (analytics.total_sessions - 1)
            analytics.avg_score = round((total + score) / analytics.total_sessions, 2)

        if analytics.best_score is None or score > analytics.best_score:
            analytics.best_score = score
        if analytics.worst_score is None or score < analytics.worst_score:
            analytics.worst_score = score

    async def _get_most_practiced_type(self, user_id: str) -> str | None:
        result = await self.db.execute(
            select(
                InterviewSession.interview_type,
                func.count(InterviewSession.id).label("cnt"),
            )
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
                InterviewSession.deleted_at.is_(None),
            )
            .group_by(InterviewSession.interview_type)
            .order_by(desc("cnt"))
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    async def check_milestones(
        self, user_id: str, session: InterviewSession, total_count: int
    ) -> None:
        """Award any newly achieved milestones."""
        for m_type, m_name, condition in MILESTONES:
            if not condition(session, total_count):
                continue
            existing = await self.db.execute(
                select(UserMilestone).where(
                    UserMilestone.user_id == user_id,
                    UserMilestone.milestone_type == m_type,
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.db.add(
                UserMilestone(
                    user_id=user_id,
                    milestone_type=m_type,
                    milestone_name=m_name,
                    achieved_at=datetime.utcnow(),
                    session_id=session.id,
                )
            )
        await self.db.commit()

    async def save_skill_scores(
        self,
        user_id: str,
        session_id: UUID,
        skills: list[KeySkill],
        overall_score: int,
    ) -> None:
        """Record per-skill score snapshot after session completion."""
        for skill in skills:
            self.db.add(
                SkillScoreHistory(
                    user_id=user_id,
                    skill_name=skill.keyword,
                    score=overall_score,
                    session_id=session_id,
                    recorded_at=datetime.utcnow(),
                )
            )
        await self.db.commit()