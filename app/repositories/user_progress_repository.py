from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics.user_progress import UserModuleProgress as UserProgress
from app.models.analytics.user_streaks import UserStreaks


class UserProgressRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_topic(
        self, user_id: str, module_name: str, topic: str, subtopic: str
    ) -> UserProgress | None:
        stmt = select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.module_name == module_name,
            UserProgress.topic == topic,
            UserProgress.subtopic == subtopic,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        module: str,
        topic: str,
        subtopic: str,
        total_attempts: int = 0,
        correct_attempts: int = 0,
        time_spent_secs: int = 0,
    ) -> UserProgress:
        up = UserProgress(
            user_id=user_id,
            module_name=module,
            topic=topic,
            subtopic=subtopic,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            time_spent_secs=time_spent_secs,
        )
        self.db.add(up)
        await self.db.commit()
        await self.db.refresh(up)
        return up

    async def save(self, record: UserProgress) -> UserProgress:
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_user_and_module(self, user_id: str, module_name: str) -> list[UserProgress]:
        stmt = (
            select(UserProgress)
            .where(
                UserProgress.user_id == user_id,
                UserProgress.module_name == module_name,
            )
            .order_by(UserProgress.last_attempt_at)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    # Streaks
    async def get_streaks_for_user(self, user_id: str) -> UserStreaks | None:
        stmt = select(UserStreaks).where(UserStreaks.user_id == user_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def save_streak(self, streak: UserStreaks) -> UserStreaks:
        self.db.add(streak)
        await self.db.commit()
        await self.db.refresh(streak)
        return streak

    async def create_streak(
        self, user_id: str, current_streak: int, longest_streak: int, last_activity_date
    ):
        s = UserStreaks(
            user_id=user_id,
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_activity_date=last_activity_date,
        )
        self.db.add(s)
        await self.db.commit()
        await self.db.refresh(s)
        return s
