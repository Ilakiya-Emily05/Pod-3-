from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Vocab.vocabulary_word import VocabularyWord
from app.models.Vocab.user_vocabulary import UserVocabulary


# =========================
# SM-2 (UPGRADED 🔥)
# =========================
def calculate_sm2(
    quality: int,
    easiness: float,
    repetitions: int,
    interval: int
):
    quality = max(0, min(5, quality))

    # FAILURE
    if quality < 3:
        return max(1.3, easiness - 0.2), 0, 1

    new_repetitions = repetitions + 1

    # INTERVAL
    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = round(interval * easiness)

    # HARD (slow down)
    if quality == 3:
        new_interval = max(1, round(new_interval * 0.75))

    # EASY (boost)
    if quality == 5:
        new_interval = round(new_interval * 1.3)

    # EF UPDATE
    new_easiness = easiness + (
        0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )

    new_easiness = max(1.3, min(new_easiness, 3.0))

    return new_easiness, new_repetitions, max(1, new_interval)


# =========================
# HELPER: MAP STRING → QUALITY
# =========================
def map_response_to_quality(response: str) -> int:
    mapping = {
        "again": 1,
        "hard": 3,
        "medium": 4,
        "easy": 5,
    }

    response = response.lower()

    if response not in mapping:
        raise ValueError(f"Invalid response: {response}")

    return mapping[response]


# =========================
# SERVICE
# =========================
class VocabularyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================
    # AI GENERATION (THRESHOLD)
    # =========================
    async def _generate_words_if_needed(self, cefr_level: str = "A1"):
        MIN_WORDS = 50

        result = await self.db.execute(
            select(func.count(VocabularyWord.word_id))
            .where(VocabularyWord.cefr_level == cefr_level)
        )
        count = result.scalar()

        if count >= MIN_WORDS:
            return

        from app.agents.ai_content_service import AIContentService

        ai = AIContentService()

        generated_words = await ai.generate_words(
            industry="IT",
            cefr_level=cefr_level,
            count=20
        )

        for w in generated_words:
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

        await self.db.commit()

    # =========================
    # GET WORDS
    # =========================
    async def get_words(self, user_id: UUID, limit: int = 10):
        now = datetime.now(timezone.utc)

        # 1. DUE WORDS
        result = await self.db.execute(
            select(UserVocabulary)
            .where(UserVocabulary.user_id == user_id)
            .where(UserVocabulary.next_review_date <= now)
            .limit(limit)
        )
        due_words = result.scalars().all()

        words: List[Tuple[UserVocabulary, VocabularyWord]] = []

        for uv in due_words:
            vw = await self.db.get(VocabularyWord, uv.word_id)
            if vw:
                words.append((uv, vw))

        # 2. NEW WORDS
        if len(words) < limit:
            needed = limit - len(words)

            subquery = select(UserVocabulary.word_id).where(
                UserVocabulary.user_id == user_id
            )

            res = await self.db.execute(
                select(VocabularyWord)
                .where(VocabularyWord.word_id.not_in(subquery))
                .limit(needed)
            )

            new_words = res.scalars().all()

            for vw in new_words:
                uv = UserVocabulary(
                    user_id=user_id,
                    word_id=vw.word_id,
                    next_review_date=now
                )
                self.db.add(uv)
                words.append((uv, vw))

            await self.db.commit()

        # =========================
        # 3. AI FALLBACK 🔥
        # =========================
        if len(words) < limit:
            await self._generate_words_if_needed("A1")

            needed = limit - len(words)

            subquery = select(UserVocabulary.word_id).where(
                UserVocabulary.user_id == user_id
            )

            res = await self.db.execute(
                select(VocabularyWord)
                .where(VocabularyWord.word_id.not_in(subquery))
                .limit(needed)
            )

            ai_words = res.scalars().all()

            for vw in ai_words:
                uv = UserVocabulary(
                    user_id=user_id,
                    word_id=vw.word_id,
                    next_review_date=now
                )
                self.db.add(uv)
                words.append((uv, vw))

            await self.db.commit()

        return words

    # =========================
    # RECORD RESPONSE
    # =========================
    async def record_response(
        self,
        user_id: UUID,
        word_id: UUID,
        response: str,
    ):
        now = datetime.now(timezone.utc)

        quality = map_response_to_quality(response)

        result = await self.db.execute(
            select(UserVocabulary).where(
                UserVocabulary.user_id == user_id,
                UserVocabulary.word_id == word_id
            )
        )
        uv = result.scalar_one_or_none()

        if not uv:
            raise ValueError("UserVocabulary not found")

        # SM-2
        new_e, new_r, new_i = calculate_sm2(
            quality,
            uv.retention_score,
            uv.repetition_count,
            uv.interval_days
        )

        uv.retention_score = new_e
        uv.repetition_count = new_r
        uv.interval_days = new_i
        uv.next_review_date = now + timedelta(days=new_i)
        uv.last_reviewed_at = now

        # stats
        if quality >= 3:
            uv.times_correct += 1
        else:
            uv.times_incorrect += 1

        # status
        if uv.repetition_count >= 5:
            uv.status = "mastered"
        elif uv.times_incorrect > uv.times_correct:
            uv.status = "struggling"
        else:
            uv.status = "learning"

        await self.db.commit()

        return {
            "word_id": word_id,
            "new_retention_score": uv.retention_score,
            "next_review_date": uv.next_review_date,
            "interval_days": uv.interval_days,
            "feedback": f"You selected '{response}'"
        }

    # =========================
    # STATS
    # =========================
    async def get_stats(self, user_id: UUID):
        result = await self.db.execute(
            select(UserVocabulary).where(UserVocabulary.user_id == user_id)
        )
        rows = result.scalars().all()

        return {
            "total_words_learned": len(rows),
            "words_mastered": sum(r.status == "mastered" for r in rows),
            "words_learning": sum(r.status == "learning" for r in rows),
            "words_struggling": sum(r.status == "struggling" for r in rows),
        }