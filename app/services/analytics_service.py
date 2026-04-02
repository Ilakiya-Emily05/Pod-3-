from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_status import AttemptStatus
from app.models.behav_assessment_model import BehavAttempt, AttemptStatus as BehavAttemptStatus
from app.models.grammar import GrammarAssessment, GrammarAttempt
from app.models.interview_system import InterviewSession
from app.models.listening import ListeningAttempt
from app.models.pronunciation_model import PronunciationResult
from app.models.reading import ReadingAttempt
from app.schemas.analytics import (
    AnalyticsModuleBreakdown,
    AnalyticsProgressResponse,
    BehavioralModuleProgress,
    GrammarModuleProgress,
    PronunciationModuleProgress,
)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_progress(self, user_id: UUID) -> AnalyticsProgressResponse:
        grammar = await self._get_grammar_module_progress(user_id)
        behavioral = await self._get_behavioral_module_progress(user_id)
        pronunciation = await self._get_pronunciation_module_progress(user_id)

        overall_completion = round(
            (
                grammar.completion_pct
                + pronunciation.completion_pct
                + (100.0 if behavioral.completed else 0.0)
            )
            / 3,
            2,
        )

        latest_cefr_level = await self._get_latest_cefr_level(user_id)
        activity_points = await self._get_activity_timestamps(user_id)
        last_activity = max(activity_points) if activity_points else None

        return AnalyticsProgressResponse(
            user_id=user_id,
            overall_completion_pct=overall_completion,
            cefr_level=latest_cefr_level,
            modules=AnalyticsModuleBreakdown(
                grammar=grammar,
                pronunciation=pronunciation,
                behavioral=behavioral,
            ),
            streak_days=self._compute_streak_days(activity_points),
            last_activity=last_activity,
        )

    async def _get_grammar_module_progress(self, user_id: UUID) -> GrammarModuleProgress:
        total_assessments_result = await self.db.execute(select(func.count(GrammarAssessment.id)))
        total_assessments = int(total_assessments_result.scalar() or 0)

        completed_query = select(func.count(func.distinct(GrammarAttempt.assessment_id))).where(
            GrammarAttempt.user_id == user_id,
            GrammarAttempt.status == AttemptStatus.SUBMITTED,
        )
        completed_result = await self.db.execute(completed_query)
        completed_assessments = int(completed_result.scalar() or 0)

        if total_assessments > 0:
            completion_pct = round((completed_assessments / total_assessments) * 100.0, 2)
        else:
            completion_pct = 0.0

        avg_accuracy_query = select(
            func.avg(
                (GrammarAttempt.correct_answers.cast(Float)
                / func.nullif(GrammarAttempt.total_questions.cast(Float), 0.0))
                * 100.0
            )
        ).where(
            GrammarAttempt.user_id == user_id,
            GrammarAttempt.status == AttemptStatus.SUBMITTED,
        )
        avg_accuracy_result = await self.db.execute(avg_accuracy_query)
        avg_score = round(float(avg_accuracy_result.scalar() or 0.0), 2)

        topic_accuracy_query = (
            select(
                GrammarAssessment.topic,
                func.avg(
                    (GrammarAttempt.correct_answers.cast(Float)
                    / func.nullif(GrammarAttempt.total_questions.cast(Float), 0.0))
                    * 100.0
                ).label("topic_avg"),
            )
            .join(GrammarAssessment, GrammarAssessment.id == GrammarAttempt.assessment_id)
            .where(
                GrammarAttempt.user_id == user_id,
                GrammarAttempt.status == AttemptStatus.SUBMITTED,
                GrammarAssessment.topic.isnot(None),
            )
            .group_by(GrammarAssessment.topic)
        )
        topic_accuracy_result = await self.db.execute(topic_accuracy_query)
        weak_topics = [
            str(topic)
            for topic, topic_avg in topic_accuracy_result.all()
            if topic is not None and topic_avg is not None and float(topic_avg) < 60.0
        ]

        return GrammarModuleProgress(
            completion_pct=completion_pct,
            avg_score=avg_score,
            weak_topics=weak_topics,
        )

    async def _get_pronunciation_module_progress(self, user_id: UUID) -> PronunciationModuleProgress:
        query = select(
            func.count(PronunciationResult.id),
            func.avg(PronunciationResult.pronunciation_score),
        ).where(PronunciationResult.user_id == user_id)
        result = await self.db.execute(query)
        attempts_count, avg_score_raw = result.one()

        attempts = int(attempts_count or 0)
        avg_score = float(avg_score_raw or 0.0)

        # Completion is normalized to a 10-attempt milestone for dashboard progress.
        completion_pct = round(min(attempts / 10.0, 1.0) * 100.0, 2)

        if attempts == 0:
            current_level = "Beginner"
        elif avg_score < 40:
            current_level = "Beginner"
        elif avg_score < 70:
            current_level = "Intermediate"
        else:
            current_level = "Advanced"

        return PronunciationModuleProgress(
            completion_pct=completion_pct,
            current_level=current_level,
        )

    async def _get_behavioral_module_progress(self, user_id: UUID) -> BehavioralModuleProgress:
        latest_behavioral_query = (
            select(BehavAttempt)
            .where(
                BehavAttempt.user_id == user_id,
                BehavAttempt.status == BehavAttemptStatus.SUBMITTED,
            )
            .order_by(BehavAttempt.submitted_at.desc())
            .limit(1)
        )
        result = await self.db.execute(latest_behavioral_query)
        latest_attempt = result.scalar_one_or_none()
        if latest_attempt is None:
            return BehavioralModuleProgress(completed=False, hexaco_summary=None)

        return BehavioralModuleProgress(completed=True, hexaco_summary=latest_attempt.scores)

    async def _get_latest_cefr_level(self, user_id: UUID) -> str | None:
        latest_points: list[tuple[datetime | None, str | None]] = []
        for attempt_model in (GrammarAttempt, ListeningAttempt, ReadingAttempt):
            query = (
                select(attempt_model.submitted_at, attempt_model.cefr_level)
                .where(
                    attempt_model.user_id == user_id,
                    attempt_model.status == AttemptStatus.SUBMITTED,
                    attempt_model.cefr_level.isnot(None),
                )
                .order_by(attempt_model.submitted_at.desc())
                .limit(1)
            )
            result = await self.db.execute(query)
            latest_points.extend((row[0], row[1]) for row in result.all())

        latest_with_level = [
            (submitted_at, cefr_level)
            for submitted_at, cefr_level in latest_points
            if submitted_at is not None and cefr_level
        ]
        if not latest_with_level:
            return None

        latest_with_level.sort(key=lambda item: item[0], reverse=True)
        return str(latest_with_level[0][1])

    async def _get_activity_timestamps(self, user_id: UUID) -> list[datetime]:
        activity: list[datetime] = []

        for model, submitted_field, started_field in (
            (GrammarAttempt, GrammarAttempt.submitted_at, GrammarAttempt.started_at),
            (ListeningAttempt, ListeningAttempt.submitted_at, ListeningAttempt.started_at),
            (ReadingAttempt, ReadingAttempt.submitted_at, ReadingAttempt.started_at),
        ):
            query = select(submitted_field, started_field).where(model.user_id == user_id)
            result = await self.db.execute(query)
            for submitted_at, started_at in result.all():
                if submitted_at is not None:
                    activity.append(submitted_at)
                elif started_at is not None:
                    activity.append(started_at)

        behav_query = select(BehavAttempt.submitted_at, BehavAttempt.created_at).where(
            BehavAttempt.user_id == user_id
        )
        behav_result = await self.db.execute(behav_query)
        for submitted_at, created_at in behav_result.all():
            if submitted_at is not None:
                activity.append(submitted_at)
            elif created_at is not None:
                activity.append(created_at)

        interview_query = select(InterviewSession.created_at).where(InterviewSession.user_id == user_id)
        interview_result = await self.db.execute(interview_query)
        activity.extend([created_at for created_at in interview_result.scalars().all() if created_at])

        pronunciation_query = select(PronunciationResult.created_at).where(
            PronunciationResult.user_id == user_id
        )
        pronunciation_result = await self.db.execute(pronunciation_query)
        activity.extend([created_at for created_at in pronunciation_result.scalars().all() if created_at])

        return activity

    def _compute_streak_days(self, activity_points: list[datetime]) -> int:
        if not activity_points:
            return 0

        unique_days = sorted({point.date() for point in activity_points}, reverse=True)
        if not unique_days:
            return 0

        streak = 1
        previous_day = unique_days[0]
        for current_day in unique_days[1:]:
            if (previous_day - current_day).days == 1:
                streak += 1
                previous_day = current_day
            else:
                break
        return streak
