from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import VocabularyWord, UserVocabulary, VocabularyList


class VocabularyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_due_for_user(self, user_id: UUID, limit: int = 20) -> List[UserVocabulary]:
        now = datetime.utcnow()
        q = (
            select(UserVocabulary)
            .where(UserVocabulary.user_id == user_id)
            .where(UserVocabulary.next_review_date <= now)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_word(self, word_id: UUID) -> Optional[VocabularyWord]:
        return await self.db.get(VocabularyWord, word_id)

    async def list_lists(self) -> List[VocabularyList]:
        res = await self.db.execute(select(VocabularyList))
        return res.scalars().all()

    async def get_list_words(self, list_id: UUID) -> List[VocabularyWord]:
        res = await self.db.execute(select(VocabularyWord).where(VocabularyWord.list_id == list_id))
        return res.scalars().all()

    async def create_user_vocab_if_missing(self, user_id: UUID, word_id: UUID) -> UserVocabulary:
        uv = await self.db.get(UserVocabulary, (user_id, word_id))
        if uv:
            return uv
        uv = UserVocabulary(
            user_id=user_id,
            word_id=word_id,
            repetition_count=0,
            easiness=2.5,
            interval_days=0,
            next_review_date=datetime.utcnow(),
            times_correct=0,
            times_incorrect=0,
        )
        self.db.add(uv)
        await self.db.flush()
        return uv


__all__ = ["VocabularyRepository"]
