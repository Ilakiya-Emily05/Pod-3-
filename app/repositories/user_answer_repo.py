from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.question import Question
from app.models.user_answer import UserAnswer


class UserAnswerRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user_answer(
        self, session_id: UUID, question_id: UUID, selected_answer: str, is_correct: bool
    ) -> UserAnswer:
        user_answer = UserAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )
        self.db.add(user_answer)
        await self.db.commit()
        await self.db.refresh(user_answer)
        return user_answer

    async def get_answers_by_session(self, session_id: UUID) -> list[UserAnswer]:
        result = await self.db.execute(
            select(UserAnswer)
            .options(joinedload(UserAnswer.question))
            .where(UserAnswer.session_id == session_id)
        )
        return list(result.scalars().all())

    async def get_attempted_question_ids(self, session_id: UUID) -> list[UUID]:
        result = await self.db.execute(
            select(UserAnswer.question_id).where(UserAnswer.session_id == session_id)
        )
        return list(result.scalars().all())

    async def count_attempted(self, session_id: UUID, topic: str, subtopic: str) -> int:
        result = await self.db.execute(
            select(Question)
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .where(
                UserAnswer.session_id == session_id,
                Question.topic == topic,
                Question.subtopic == subtopic,
            )
        )
        return len(result.scalars().all())
