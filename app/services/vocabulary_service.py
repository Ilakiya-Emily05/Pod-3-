from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import VocabularyWord, UserVocabulary, VocabularyList


def _sm2_next_interval(rep: int, quality: int, easiness: float) -> tuple[int, float]:
    # returns (interval_days, new_easiness)
    if quality < 3:
        return 0, max(1.3, easiness - 0.2)

    if rep == 0:
        interval = 1
    elif rep == 1:
        interval = 6
    else:
        interval = round((rep - 1) * easiness)

    new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_easiness < 1.3:
        new_easiness = 1.3

    return interval, new_easiness


class VocabularyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_due_words(self, user_id: UUID, limit: int = 20) -> List[VocabularyWord]:
        q = (
            select(UserVocabulary)
            .where(UserVocabulary.user_id == user_id)
            .where(UserVocabulary.next_review_date <= datetime.utcnow())
            .limit(limit)
        )
        res = await self.db.execute(q)
        rows = res.scalars().all()
        # load VocabularyWord objects for each
        words = []
        for uv in rows:
            vw = await self.db.get(VocabularyWord, uv.word_id)
            if vw:
                words.append((uv, vw))
        return words

    async def record_response(self, user_id: UUID, word_id: UUID, quality: int, response_time_ms: int):
        uv = await self.db.get(UserVocabulary, (user_id, word_id))
        now = datetime.utcnow()
        if uv is None:
            # initialize
            uv = UserVocabulary(
                user_id=user_id,
                word_id=word_id,
                repetition_count=0,
                easiness=2.5,
                interval_days=0,
                next_review_date=now,
                times_correct=0,
                times_incorrect=0,
            )
            self.db.add(uv)

        if quality >= 3:
            uv.repetition_count += 1
            uv.times_correct += 1
        else:
            uv.repetition_count = 0
            uv.times_incorrect += 1

        interval, new_easiness = _sm2_next_interval(uv.repetition_count, quality, uv.easiness)
        uv.easiness = new_easiness
        uv.interval_days = interval
        uv.next_review_date = now + timedelta(days=interval) if interval > 0 else now + timedelta(days=1)
        uv.last_reviewed = now

        await self.db.commit()
        return {
            "word_id": word_id,
            "new_retention_score": uv.easiness,
            "next_review_date": uv.next_review_date,
            "interval_days": uv.interval_days,
        }

    async def list_word_lists(self) -> List[VocabularyList]:
        res = await self.db.execute(select(VocabularyList))
        return res.scalars().all()

    async def start_list_for_user(self, list_id: UUID, user_id: UUID) -> int:
        # Create UserVocabulary entries for all words in the list
        words = await self.db.execute(select(VocabularyWord).where(VocabularyWord.list_id == list_id))
        words = words.scalars().all()
        count = 0
        now = datetime.utcnow()
        for w in words:
            existing = await self.db.get(UserVocabulary, (user_id, w.id))
            if existing:
                continue
            uv = UserVocabulary(
                user_id=user_id,
                word_id=w.id,
                repetition_count=0,
                easiness=2.5,
                interval_days=0,
                next_review_date=now,
                times_correct=0,
                times_incorrect=0,
            )
            self.db.add(uv)
            count += 1

        await self.db.commit()
        return count


__all__ = ["VocabularyService"]
