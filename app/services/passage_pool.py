import asyncio
import random
import threading

from sqlalchemy.orm import Session

from app.agents.tools.passage_tool import generate_passage_with_questions
from app.config.database import get_db
from app.repositories.passage_repo import PassageRepository

MIN_POOL = 10
LOW_BUFFER = 5
MAX_POOL = 50
CONCURRENCY = 5
TOPIC_HINTS = [
    "school life",
    "family routines",
    "city transport",
    "local markets",
    "sports practice",
    "healthy habits",
    "technology in daily life",
    "environmental awareness",
    "community events",
    "travel experiences",
]

READING_POOL: list[int] = []
READING_POOL_SET: set[int] = set()
POOL_LOCK = threading.Lock()
REFILL_TASK: asyncio.Task | None = None
GENERATION_SEMAPHORE = asyncio.Semaphore(CONCURRENCY)


def _pool_size() -> int:
    with POOL_LOCK:
        return len(READING_POOL)


def _push_passage_ids(passage_ids: list[int]) -> None:
    with POOL_LOCK:
        for passage_id in passage_ids:
            if passage_id in READING_POOL_SET:
                continue
            READING_POOL.append(passage_id)
            READING_POOL_SET.add(passage_id)


def take_random_passage_id() -> int | None:
    with POOL_LOCK:
        if not READING_POOL:
            return None

        index = random.randrange(len(READING_POOL))
        passage_id = READING_POOL.pop(index)
        READING_POOL_SET.discard(passage_id)
        return passage_id


async def _seed_from_existing_passages(db: Session, limit: int) -> int:
    repo = PassageRepository(db)
    seeded_ids: list[int] = []

    for passage in await repo.get_eligible_passages(limit=limit):
        if passage.id in READING_POOL_SET:
            continue
        seeded_ids.append(passage.id)

    _push_passage_ids(seeded_ids)
    return len(seeded_ids)


async def _safe_generate(topic_hint: str | None = None) -> dict:
    async with GENERATION_SEMAPHORE:
        topic = topic_hint or random.choice(TOPIC_HINTS)
        return await asyncio.to_thread(generate_passage_with_questions, topic)


async def _generate_batch(batch_size: int, topic_hint: str | None = None) -> list[dict]:
    tasks = [asyncio.create_task(_safe_generate(topic_hint)) for _ in range(batch_size)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [result for result in results if not isinstance(result, Exception)]


async def _store_generated_result(repo: PassageRepository, result: dict) -> int | None:
    passage_text = result.get("passage")
    questions = result.get("questions", [])

    if not passage_text or not questions:
        return None

    if repo.passage_text_exists(passage_text):
        return None

    unique_questions: list[dict] = []
    for question in questions:
        question_text = question.get("question")
        if not question_text or repo.question_text_exists(question_text):
            continue
        if not question.get("options"):
            continue
        unique_questions.append(question)

    if len(unique_questions) != 5:
        return None

    if not _validate_distribution(unique_questions):
        return None

    passage = await repo.create_passage(passage_text)
    for question in unique_questions:
        await repo.create_passage_question(
            passage_id=passage.id,
            question_text=question["question"],
            options=question["options"],
            correct_answer=question["correct_answer"],
            difficulty=question["difficulty"],
        )

    return passage.id


async def fill_pool(target_size: int) -> None:
    db_gen = get_db()
    db = await anext(db_gen)
    repo = PassageRepository(db)

    try:
        current_size = _pool_size()
        missing = max(0, target_size - current_size)
        if missing <= 0:
            return

        generated_ids: list[int] = []
        attempts = 0
        max_attempts = max(missing * 3, missing + 2)

        while len(generated_ids) < missing and attempts < max_attempts:
            attempts += 1
            if await repo.count_passages() >= MAX_POOL:
                break

            batch_size = min(
                CONCURRENCY,
                missing - len(generated_ids),
                MAX_POOL - await repo.count_passages(),
            )
            if batch_size <= 0:
                break

            for result in await _generate_batch(batch_size):
                passage_id = await _store_generated_result(repo, result)
                if passage_id:
                    generated_ids.append(passage_id)

        _push_passage_ids(generated_ids)
    finally:
        await db_gen.aclose()


async def preload_initial_pool() -> None:
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        await _seed_from_existing_passages(db, MIN_POOL)
        await fill_pool(MIN_POOL)
    finally:
        await db_gen.aclose()


async def refill_pool_loop() -> None:
    while True:
        current_size = _pool_size()
        if current_size < LOW_BUFFER:
            await fill_pool(MAX_POOL)

        await asyncio.sleep(1)


def _validate_distribution(questions: list[dict]) -> bool:
    count = {"easy": 0, "medium": 0, "hard": 0}
    for question in questions:
        difficulty = question.get("difficulty", "medium")
        if difficulty in count:
            count[difficulty] += 1
    return count == {"easy": 2, "medium": 2, "hard": 1}
