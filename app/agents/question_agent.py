from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.agents.ai_generator import AIGeneratorService
    from app.repositories.question_repo import QuestionRepository
    from app.repositories.user_answer_repo import UserAnswerRepository


class QuestionAgent:
    MIN_POOL = 25
    LOW_BUFFER = 5

    def __init__(
        self,
        question_repo: QuestionRepository,
        answer_repo: UserAnswerRepository,
        ai_generator: AIGeneratorService,
    ) -> None:
        self.question_repo = question_repo
        self.answer_repo = answer_repo
        self.ai = ai_generator

    def ensure_questions(self, topic: str, subtopic: str, session_id: int | None = None) -> None:
        total = self.question_repo.count_by_topic_subtopic(topic, subtopic)

        if session_id is None:
            if total < self.MIN_POOL:
                self._generate(topic, subtopic, self.MIN_POOL - total)
            return None

        attempted = self.answer_repo.count_attempted(session_id, topic, subtopic)
        available = total - attempted

        if total < self.MIN_POOL:
            self._generate(topic, subtopic, self.MIN_POOL - total)
            return None

        if available < self.LOW_BUFFER:
            self._generate(topic, subtopic, 10)
            return None

        return None

    def _generate(self, topic: str, subtopic: str, count: int) -> None:
        logger.info(
            "Starting generation for %s/%s: requesting %s questions", topic, subtopic, count
        )
        chunk = 5
        remaining = count
        all_new: list[dict[str, object]] = []

        while remaining > 0:
            to_request = min(chunk, remaining)
            try:
                batch = self.ai.generate_questions(
                    topic=topic, subtopic=subtopic, difficulty="medium", count=to_request
                )
                logger.debug("Batch request returned %s questions", len(batch) if batch else 0)
            except Exception as err:
                logger.exception("Generation failed in batch loop: %s", err)
                break

            if not batch:
                logger.warning("Empty batch returned for %s/%s", topic, subtopic)
                break

            batch_unique = []
            existing = set(self.question_repo.get_all_question_texts()) | {
                str(q.get("question")) for q in all_new if q.get("question") is not None
            }
            for q in batch:
                text = q.get("question")
                if not isinstance(text, str) or text in existing:
                    continue
                batch_unique.append(q)
                existing.add(text)

            if batch_unique:
                self.question_repo.bulk_insert(topic, subtopic, batch_unique)
                logger.info(
                    "Inserted %s unique questions for %s/%s",
                    len(batch_unique),
                    topic,
                    subtopic,
                )
                all_new.extend(batch_unique)

            remaining -= to_request

        logger.info(
            "Generation complete: inserted %s total questions for %s/%s",
            len(all_new),
            topic,
            subtopic,
        )
