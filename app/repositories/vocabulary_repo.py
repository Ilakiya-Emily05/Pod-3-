from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Vocab.vocabulary_session import VocabularySession
from app.models.Vocab.vocabulary_word import VocabularyWord
from app.models.Vocab.user_vocabulary import UserVocabulary


class VocabularyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================
    # USER VOCAB
    # =========================
    async def create_session(self, user_id: UUID):
        session = VocabularySession(user_id=user_id)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: UUID):
        return await self.db.get(VocabularySession, session_id)

    async def get_due_words(self, user_id: UUID, now: datetime, limit: int):
        result = await self.db.execute(
            select(UserVocabulary)
            .where(UserVocabulary.user_id == user_id)
            .where(UserVocabulary.next_review_date <= now)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_user_vocab(self, user_id: UUID, word_id: UUID):
        result = await self.db.execute(
            select(UserVocabulary).where(
                UserVocabulary.user_id == user_id,
                UserVocabulary.word_id == word_id
            )
        )
        return result.scalar_one_or_none()

    async def create_user_vocab(self, user_id: UUID, word_id: UUID, now: datetime):
        uv = UserVocabulary(
            user_id=user_id,
            word_id=word_id,
            next_review_date=now
        )
        self.db.add(uv)
        return uv

    # =========================
    # VOCAB WORDS
    # =========================
    async def get_new_words(self, user_id: UUID, limit: int):
        subquery = select(UserVocabulary.word_id).where(
            UserVocabulary.user_id == user_id
        )

        result = await self.db.execute(
            select(VocabularyWord)
            .where(VocabularyWord.word_id.not_in(subquery))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_word_by_id(self, word_id: UUID):
        return await self.db.get(VocabularyWord, word_id)

    async def count_words_by_level(self, cefr_level: str):
        result = await self.db.execute(
            select(func.count(VocabularyWord.word_id))
            .where(VocabularyWord.cefr_level == cefr_level)
        )
        return result.scalar()

    async def insert_words(self, words: list[dict], cefr_level: str):
        for w in words:
            if not w.get("word") or not w.get("definition"):
                continue

            vw = VocabularyWord(
                word=w["word"],
                definition=w["definition"],
                cefr_level=cefr_level,
                industry="IT",
                example_sentence=w.get("example_sentence"),
            )
            self.db.add(vw)

    # =========================
    # STATS
    # =========================
    async def get_user_vocab_all(self, user_id: UUID):
        result = await self.db.execute(
            select(UserVocabulary).where(UserVocabulary.user_id == user_id)
        )
        return result.scalars().all()

    # =========================
    # COMMIT
    # =========================
    async def commit(self):
        await self.db.commit()