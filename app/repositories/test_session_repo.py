from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_session import TestSession


class TestSessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, user_id: UUID, topic: str, subtopic: str) -> TestSession:
        session = TestSession(
            user_id=user_id,
            current_topic=topic,
            current_subtopic=subtopic,
            question_index=0,
            correct_count=0,
            total_questions=0,
            status="IN_PROGRESS",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: UUID) -> TestSession | None:
        result = await self.db.execute(select(TestSession).where(TestSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_active_session(self, user_id: UUID) -> TestSession | None:
        result = await self.db.execute(
            select(TestSession).where(
                TestSession.user_id == user_id,
                TestSession.status == "IN_PROGRESS",
            )
        )
        return result.scalar_one_or_none()

    async def update(self, session: TestSession) -> TestSession:
        await self.db.commit()
        await self.db.refresh(session)
        return session
