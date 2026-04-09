from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question

if TYPE_CHECKING:
    from collections.abc import Sequence


class QuestionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_question(self, question_data: dict[str, object]) -> Question:
        question = Question(**question_data)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def get_question_by_id(self, question_id: UUID) -> Question | None:
        result = await self.db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def get_questions_by_topic(self, topic: str) -> list[Question]:
        result = await self.db.execute(select(Question).where(Question.topic == topic))
        return list(result.scalars().all())

    async def get_questions_by_subtopic(self, topic: str, subtopic: str) -> list[Question]:
        result = await self.db.execute(
            select(Question).where(Question.topic == topic, Question.subtopic == subtopic)
        )
        return list(result.scalars().all())

    async def get_questions_by_topic_and_subtopic(
        self, topic: str, subtopic: str, limit: int
    ) -> list[Question]:
        result = await self.db.execute(
            select(Question)
            .where(Question.topic == topic, Question.subtopic == subtopic)
            .order_by(func.random())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(self, topic: str, subtopic: str, limit: int) -> list[Question]:
        stmt = select(Question).where(Question.topic == topic, Question.subtopic == subtopic)
        if hasattr(Question, "is_active"):
            stmt = stmt.where(Question.is_active.is_(True))
        result = await self.db.execute(stmt.order_by(func.random()).limit(limit))
        return list(result.scalars().all())

    async def get_random_question(
        self, topic: str, subtopic: str, exclude_ids: list[UUID]
    ) -> Question | None:
        stmt = select(Question).where(Question.topic == topic, Question.subtopic == subtopic)
        if exclude_ids:
            stmt = stmt.where(~Question.id.in_(exclude_ids))
        result = await self.db.execute(stmt.order_by(func.random()).limit(1))
        return result.scalar_one_or_none()

    async def count_by_topic_subtopic(self, topic: str, subtopic: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Question)
            .where(Question.topic == topic, Question.subtopic == subtopic)
        )
        return int(result.scalar_one())

    async def get_all_question_texts(self) -> list[str]:
        result = await self.db.execute(select(Question.question_text))
        return list(result.scalars().all())

    async def bulk_insert(
        self, topic: str, subtopic: str, questions: Sequence[dict[str, object]]
    ) -> None:
        objs = []
        for q in questions:
            objs.append(
                Question(
                    topic=topic,
                    subtopic=subtopic,
                    question_text=q["question"],
                    options=q.get("options", {}),
                    correct_answer=q.get("correct_answer", "a"),
                )
            )
        self.db.add_all(objs)
        await self.db.commit()
