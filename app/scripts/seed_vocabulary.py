import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.config.database import Base, async_engine, async_session_maker
from app.models.Vocab.vocabulary_list import VocabularyList
from app.models.Vocab.vocabulary_word import VocabularyWord


WORDS = [
    # A1 Level (basic)
    {"word": "analyze", "definition": "to examine something carefully", "cefr": "A1"},
    {"word": "build", "definition": "to construct or create", "cefr": "A1"},
    {"word": "check", "definition": "to verify or examine", "cefr": "A1"},
    {"word": "create", "definition": "to make something new", "cefr": "A1"},
    {"word": "define", "definition": "to explain the meaning", "cefr": "A1"},
    {"word": "design", "definition": "to plan something", "cefr": "A1"},
    {"word": "develop", "definition": "to improve or grow", "cefr": "A1"},
    {"word": "fix", "definition": "to repair something", "cefr": "A1"},
    {"word": "help", "definition": "to assist someone", "cefr": "A1"},
    {"word": "learn", "definition": "to gain knowledge", "cefr": "A1"},

    # A2 Level
    {"word": "update", "definition": "to make something current", "cefr": "A2"},
    {"word": "improve", "definition": "to make better", "cefr": "A2"},
    {"word": "support", "definition": "to assist or help", "cefr": "A2"},
    {"word": "manage", "definition": "to handle or control", "cefr": "A2"},
    {"word": "organize", "definition": "to arrange properly", "cefr": "A2"},
    {"word": "connect", "definition": "to link together", "cefr": "A2"},
    {"word": "control", "definition": "to direct or manage", "cefr": "A2"},
    {"word": "deliver", "definition": "to provide something", "cefr": "A2"},
    {"word": "prepare", "definition": "to get ready", "cefr": "A2"},
    {"word": "review", "definition": "to check again", "cefr": "A2"},

    # B1 Level (intermediate)
    {"word": "stakeholder", "definition": "a person with interest in a project", "cefr": "B1"},
    {"word": "requirement", "definition": "something needed", "cefr": "B1"},
    {"word": "deadline", "definition": "time limit to finish work", "cefr": "B1"},
    {"word": "strategy", "definition": "a plan to achieve a goal", "cefr": "B1"},
    {"word": "process", "definition": "a series of steps", "cefr": "B1"},
    {"word": "resource", "definition": "something used to complete a task", "cefr": "B1"},
    {"word": "performance", "definition": "how well something works", "cefr": "B1"},
    {"word": "solution", "definition": "answer to a problem", "cefr": "B1"},
    {"word": "approach", "definition": "a way of doing something", "cefr": "B1"},
    {"word": "feedback", "definition": "response or opinion", "cefr": "B1"},

    # B2 Level
    {"word": "optimization", "definition": "making something as effective as possible", "cefr": "B2"},
    {"word": "scalability", "definition": "ability to handle growth", "cefr": "B2"},
    {"word": "integration", "definition": "combining systems together", "cefr": "B2"},
    {"word": "architecture", "definition": "system design structure", "cefr": "B2"},
    {"word": "automation", "definition": "using machines to do tasks", "cefr": "B2"},
    {"word": "efficiency", "definition": "doing something with minimal waste", "cefr": "B2"},
    {"word": "deployment", "definition": "releasing software to users", "cefr": "B2"},
    {"word": "configuration", "definition": "system setup", "cefr": "B2"},
    {"word": "maintenance", "definition": "keeping system working", "cefr": "B2"},
    {"word": "analysis", "definition": "detailed examination", "cefr": "B2"},
]

WORDS = WORDS * 3


def build_example(word: str) -> str:
    return f"This is an example sentence using the word '{word}'."


async def seed() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                bind=sync_conn,
                tables=[VocabularyList.__table__, VocabularyWord.__table__],
                checkfirst=True,
            )
        )

    async with async_session_maker() as db:
        existing_rows = await db.execute(select(VocabularyWord.word, VocabularyWord.cefr_level))
        existing_pairs = set(existing_rows.all())

        inserted = 0
        skipped = 0

        for word_data in WORDS:
            word_key = (word_data["word"], word_data["cefr"])
            if word_key in existing_pairs:
                skipped += 1
                continue

            vocab = VocabularyWord(
                word_id=uuid4(),
                word=word_data["word"],
                definition=word_data["definition"],
                cefr_level=word_data["cefr"],
                industry="IT",
                example_sentence=build_example(word_data["word"]),
            )
            db.add(vocab)
            existing_pairs.add(word_key)
            inserted += 1

        await db.commit()
        print(f"Seed completed: inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
