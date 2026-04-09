from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.passage import Passage
from app.models.passage_answer import PassageAnswer
from app.models.passage_question import ComprehensionQuestion
from app.models.passage_session import PassageSession


class PassageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_passage(self, text: str) -> Passage:
        passage = Passage(text=text)
        self.db.add(passage)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(passage)
        return passage

    async def get_passage_by_id(self, passage_id: UUID) -> Passage | None:
        result = await self.db.execute(select(Passage).where(Passage.id == passage_id))
        return result.scalar_one_or_none()

    async def get_random_passage(self) -> Passage | None:
        result = await self.db.execute(select(Passage).order_by(func.random()).limit(1))
        return result.scalar_one_or_none()

    async def get_random_passage_with_questions(self, min_questions: int = 5) -> Passage | None:
        result = await self.db.execute(
            select(Passage)
            .join(ComprehensionQuestion, Passage.id == ComprehensionQuestion.passage_id)
            .group_by(Passage.id)
            .having(func.count(ComprehensionQuestion.id) >= min_questions)
            .order_by(func.random())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_eligible_passages(self, limit: int = 10) -> list[Passage]:
        result = await self.db.execute(
            select(Passage)
            .join(ComprehensionQuestion, Passage.id == ComprehensionQuestion.passage_id)
            .group_by(Passage.id)
            .having(func.count(ComprehensionQuestion.id) >= 5)
            .order_by(func.random())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_passages(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Passage))
        return int(result.scalar_one())

    async def passage_text_exists(self, text: str) -> bool:
        result = await self.db.execute(select(Passage).where(Passage.text == text))
        return result.scalar_one_or_none() is not None

    async def create_passage_session(self, user_id: UUID, passage_id: UUID) -> PassageSession:
        session = PassageSession(user_id=user_id, passage_id=passage_id)
        self.db.add(session)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_passage_session(self, session_id: UUID) -> PassageSession | None:
        result = await self.db.execute(
            select(PassageSession).where(PassageSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_passage_question(
        self,
        passage_id: UUID,
        question_text: str,
        options: dict,
        correct_answer: str,
        difficulty: str,
    ) -> ComprehensionQuestion:
        question = ComprehensionQuestion(
            passage_id=passage_id,
            question=question_text,
            options=options,
            correct_answer=correct_answer,
            difficulty=difficulty,
        )
        self.db.add(question)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def get_questions_by_passage(
        self, passage_id: UUID, limit: int = 5
    ) -> list[ComprehensionQuestion]:
        result = await self.db.execute(
            select(ComprehensionQuestion)
            .where(ComprehensionQuestion.passage_id == passage_id)
            .order_by(func.random())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_questions_by_passage(self, passage_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ComprehensionQuestion)
            .where(ComprehensionQuestion.passage_id == passage_id)
        )
        return int(result.scalar_one())

    async def get_all_question_texts(self, passage_id: UUID) -> list[str]:
        result = await self.db.execute(
            select(ComprehensionQuestion.question).where(ComprehensionQuestion.passage_id == passage_id)
        )
        return list(result.scalars().all())

    async def get_question_by_id(self, question_id: UUID) -> ComprehensionQuestion | None:
        result = await self.db.execute(
            select(ComprehensionQuestion).where(ComprehensionQuestion.id == question_id)
        )
        return result.scalar_one_or_none()

    async def question_text_exists(self, question_text: str) -> bool:
        result = await self.db.execute(
            select(ComprehensionQuestion).where(ComprehensionQuestion.question == question_text)
        )
        return result.scalar_one_or_none() is not None

    async def create_passage_answer(
        self, session_id: UUID, question_id: UUID, selected_answer: str, is_correct: bool
    ) -> PassageAnswer:
        answer = PassageAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )
        self.db.add(answer)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def get_answers_by_session(self, session_id: UUID) -> list[PassageAnswer]:
        result = await self.db.execute(
            select(PassageAnswer).where(PassageAnswer.session_id == session_id)
        )
        return result.scalars().all()

    async def count_attempted_questions(self, session_id: UUID, passage_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(PassageAnswer)
            .join(ComprehensionQuestion, ComprehensionQuestion.id == PassageAnswer.question_id)
            .where(
                PassageAnswer.session_id == session_id,
                ComprehensionQuestion.passage_id == passage_id,
            )
        )
        return int(result.scalar_one())
