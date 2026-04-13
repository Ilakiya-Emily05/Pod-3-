from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_progress_repository import UserProgressRepository

if TYPE_CHECKING:
    from app.models.analytics.user_progress import UserModuleProgress as UserProgress


def calculate_mastery(total_attempts: int, accuracy_pct: float, correct_streak: int = 0) -> bool:
    return accuracy_pct >= 80 and total_attempts >= 5 and correct_streak >= 3


class ProgressService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserProgressRepository(db)

    async def record_progress(
        self,
        user_id: str,
        module: str,
        topic: str,
        subtopic: str,
        is_correct: bool,
        time_spent_secs: int,
    ) -> dict:
        # fetch existing record
        record: UserProgress | None = await self.repo.get_by_user_topic(
            user_id, module, topic, subtopic
        )

        if record:
            record.total_attempts = (record.total_attempts or 0) + 1
            record.correct_attempts = (record.correct_attempts or 0) + (1 if is_correct else 0)
            record.time_spent_secs = (record.time_spent_secs or 0) + (time_spent_secs or 0)
        else:
            record = await self.repo.create(
                user_id=user_id,
                module=module,
                topic=topic,
                subtopic=subtopic,
                total_attempts=1,
                correct_attempts=(1 if is_correct else 0),
                time_spent_secs=(time_spent_secs or 0),
            )

        # recalc accuracy
        total = record.total_attempts or 0
        correct = record.correct_attempts or 0
        accuracy = 0.0
        if total > 0:
            accuracy = round((correct / total) * 100, 2)
        record.accuracy_pct = accuracy

        # naive correct streak calc: not persisted granularly; assume recent attempts can indicate streak
        # For a robust correct_streak we'd need attempt history; use correct_attempts heuristic here
        correct_streak = min(record.correct_attempts or 0, 5)
        record.mastery_achieved = calculate_mastery(total, accuracy, correct_streak)

        record.last_attempt_at = date.today()

        await self.repo.save(record)

        # update streaks
        streak = await self.repo.get_streaks_for_user(user_id)
        today = date.today()
        yesterday = today - timedelta(days=1)
        if streak:
            if streak.last_activity_date == yesterday:
                streak.current_streak = (streak.current_streak or 0) + 1
            elif streak.last_activity_date == today:
                pass
            else:
                streak.current_streak = 1

            if (streak.longest_streak or 0) < streak.current_streak:
                streak.longest_streak = streak.current_streak

            streak.last_activity_date = today
            await self.repo.save_streak(streak)
        else:
            await self.repo.create_streak(
                user_id=user_id, current_streak=1, longest_streak=1, last_activity_date=today
            )

        return {
            "user_id": user_id,
            "module": module,
            "topic": topic,
            "subtopic": subtopic,
            "total_attempts": record.total_attempts,
            "correct_attempts": record.correct_attempts,
            "accuracy_pct": float(record.accuracy_pct or 0),
            "mastery_achieved": bool(record.mastery_achieved),
        }

    async def get_module_details(self, user_id: str, module: str) -> dict:
        # mark activity when a user requests module details (counts as interaction)
        await self.touch_activity(user_id)
        records = await self.repo.get_by_user_and_module(user_id, module_name=module)
        payload = []
        for r in records:
            payload.append(
                {
                    "topic": r.topic,
                    "subtopic": r.subtopic,
                    "total_attempts": r.total_attempts,
                    "correct_attempts": r.correct_attempts,
                    "accuracy_pct": float(r.accuracy_pct or 0),
                    "mastery_achieved": bool(r.mastery_achieved),
                }
            )

        return {"user_id": user_id, "module": module, "data": payload}

    async def touch_activity(self, user_id: str) -> None:
        """Idempotent: register today's activity for streak tracking.

        - If user has a streak and last_activity_date == yesterday -> increment current_streak
        - If last_activity_date == today -> no-op
        - Otherwise set current_streak = 1
        """
        streak = await self.repo.get_streaks_for_user(user_id)
        today = date.today()
        yesterday = today - timedelta(days=1)
        if streak:
            if streak.last_activity_date == yesterday:
                streak.current_streak = (streak.current_streak or 0) + 1
            elif streak.last_activity_date == today:
                # already counted today
                return
            else:
                streak.current_streak = 1

            if (streak.longest_streak or 0) < streak.current_streak:
                streak.longest_streak = streak.current_streak

            streak.last_activity_date = today
            await self.repo.save_streak(streak)
        else:
            await self.repo.create_streak(
                user_id=user_id, current_streak=1, longest_streak=1, last_activity_date=today
            )

    async def get_summary(self, user_id: str) -> dict:
        # gather grammar and behavioral summaries
        grammar_recs = await self.repo.get_by_user_and_module(user_id, module_name="grammar")
        reading_recs = await self.repo.get_by_user_and_module(user_id, module_name="reading")

        def summarize(records):
            if not records:
                return None
            topics = {r.topic for r in records}
            total_topics = len(topics)
            completed_topics = len([r for r in records if r.mastery_achieved])
            avg_accuracy = (
                round(sum(float(r.accuracy_pct or 0) for r in records) / len(records), 1)
                if records
                else 0.0
            )
            total_time_secs = sum((r.time_spent_secs or 0) for r in records)
            time_spent_mins = int(total_time_secs / 60)
            if avg_accuracy >= 90:
                mastery_level = "advanced"
            elif avg_accuracy >= 75:
                mastery_level = "intermediate"
            else:
                mastery_level = "beginner"

            return {
                "total_topics": total_topics,
                "completed_topics": completed_topics,
                "completion_pct": round((completed_topics / total_topics) * 100, 1)
                if total_topics
                else 0.0,
                "avg_accuracy": avg_accuracy,
                "time_spent_mins": time_spent_mins,
                "mastery_level": mastery_level,
                "last_activity": records[-1].last_attempt_at.isoformat()
                if records and records[-1].last_attempt_at
                else None,
            }

        grammar_summary = summarize(grammar_recs) or {}
        reading_summary = summarize(reading_recs) or {}

        # overall
        overall_completion = 0.0
        if grammar_summary and reading_summary:
            overall_completion = round(
                (
                    grammar_summary.get("completion_pct", 0)
                    + reading_summary.get("completion_pct", 0)
                )
                / 2,
                1,
            )
        elif grammar_summary:
            overall_completion = grammar_summary.get("completion_pct", 0)
        elif reading_summary:
            overall_completion = reading_summary.get("completion_pct", 0)

        streak = await self.repo.get_streaks_for_user(user_id)
        streak_days = streak.current_streak if streak else 0

        return {
            "user_id": user_id,
            "modules": {
                "grammar": grammar_summary,
                "reading": reading_summary,
            },
            "overall_completion_pct": overall_completion,
            "streak_days": streak_days,
        }

    async def get_streaks(self, user_id: str) -> dict:
        streak = await self.repo.get_streaks_for_user(user_id)
        if not streak:
            return {"user_id": user_id, "current_streak": 0, "longest_streak": 0}
        return {
            "user_id": user_id,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "last_activity_date": streak.last_activity_date.isoformat()
            if streak.last_activity_date
            else None,
        }
