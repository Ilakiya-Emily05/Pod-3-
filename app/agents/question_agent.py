import logging

logger = logging.getLogger(__name__)


class QuestionAgent:
    MIN_POOL = 25
    LOW_BUFFER = 5

    def __init__(self, question_repo, answer_repo, ai_generator):
        self.question_repo = question_repo
        self.answer_repo = answer_repo
        self.ai = ai_generator

    def ensure_questions(self, topic, subtopic, session_id=None):
        total = self.question_repo.count_by_topic_subtopic(topic, subtopic)

        if session_id is None:
            if total < self.MIN_POOL:
                return self._generate(topic, subtopic, self.MIN_POOL - total)
            return

        attempted = self.answer_repo.count_attempted(session_id, topic, subtopic)
        available = total - attempted

        if total < self.MIN_POOL:
            return self._generate(topic, subtopic, self.MIN_POOL - total)

        if available < self.LOW_BUFFER:
            return self._generate(topic, subtopic, 10)

        return

    def _generate(self, topic, subtopic, count):
        logger.info(f"Starting generation for {topic}/{subtopic}: requesting {count} questions")
        chunk = 5
        remaining = count
        all_new = []

        while remaining > 0:
            to_request = min(chunk, remaining)
            try:
                batch = self.ai.generate_questions(topic=topic, subtopic=subtopic, difficulty="medium", count=to_request)
                logger.debug(f"Batch request returned {len(batch) if batch else 0} questions")
            except Exception as e:
                logger.error(f"Generation failed in batch loop: {type(e).__name__}: {str(e)}")
                break

            if not batch:
                logger.warning(f"Empty batch returned for {topic}/{subtopic}")
                break

            batch_unique = []
            existing = set(self.question_repo.get_all_question_texts()) | {q["question"] for q in all_new}
            for q in batch:
                text = q.get("question")
                if not text or text in existing:
                    continue
                batch_unique.append(q)
                existing.add(text)

            if batch_unique:
                self.question_repo.bulk_insert(topic, subtopic, batch_unique)
                logger.info(f"Inserted {len(batch_unique)} unique questions for {topic}/{subtopic}")
                all_new.extend(batch_unique)

            remaining -= to_request

        logger.info(f"Generation complete: inserted {len(all_new)} total questions for {topic}/{subtopic}")
