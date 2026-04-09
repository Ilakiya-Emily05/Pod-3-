import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database import Base
from app.models.pronunciation import PhonemePerformance, UserPronunciationProfile
from app.repositories.pronunciation import get_or_create_profile
from app.services.post_ex_service import post_exercise_hook

# ── Use a real PostgreSQL test database ───────────────────────────────────────
TEST_DB_URL = "postgresql://postgres:password@localhost:5432/test_phenomes"


@pytest.fixture(scope="function")
def db():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)  # create all tables
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)  # clean up after each test


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def phoneme_results():
    return [
        {
            "phoneme": "p",
            "correct": True,
            "accuracy": 100.0,
            "total_attempts": 1,
            "correct_attempts": 1,
        },
        {
            "phoneme": "æ",
            "correct": False,
            "accuracy": 0.0,
            "total_attempts": 1,
            "correct_attempts": 0,
        },
        {
            "phoneme": "s",
            "correct": True,
            "accuracy": 100.0,
            "total_attempts": 1,
            "correct_attempts": 1,
        },
        {
            "phoneme": "ə",
            "correct": False,
            "accuracy": 0.0,
            "total_attempts": 1,
            "correct_attempts": 0,
        },
    ]


class TestPronunciationPipeline:
    def test_profile_created_on_first_exercise(self, db, user_id):
        profile = get_or_create_profile(db, user_id)
        db.commit()
        assert profile.user_id == user_id
        assert profile.current_level == "basic"
        assert profile.exercises_completed == 0

    def test_post_exercise_hook_increments_exercises(self, db, user_id, phoneme_results):
        get_or_create_profile(db, user_id)
        db.commit()

        result = post_exercise_hook(
            db=db,
            user_id=user_id,
            phoneme_results=phoneme_results,
            time_spent_secs=30,
            current_score=75.0,
        )

        assert result["status"] == "success"
        profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
        assert profile.exercises_completed == 1
        assert profile.time_spent_total_secs == 30

    def test_phoneme_stats_upserted_correctly(self, db, user_id, phoneme_results):
        get_or_create_profile(db, user_id)
        db.commit()

        # Run twice — should accumulate not duplicate
        post_exercise_hook(db, user_id, phoneme_results, 30, 75.0)
        post_exercise_hook(db, user_id, phoneme_results, 30, 75.0)

        rows = db.query(PhonemePerformance).filter_by(user_id=user_id).all()
        phonemes = [r.phoneme for r in rows]

        # No duplicates
        assert len(phonemes) == len(set(phonemes))

        # p should have 2 total attempts
        p_row = next(r for r in rows if r.phoneme == "p")
        assert p_row.total_attempts == 2
        assert p_row.correct_attempts == 2

    def test_weak_phonemes_identified(self, db, user_id, phoneme_results):
        get_or_create_profile(db, user_id)
        db.commit()
        post_exercise_hook(db, user_id, phoneme_results, 30, 40.0)

        profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
        weak = [w["phoneme"] for w in (profile.weak_phonemes or [])]
        assert "æ" in weak
        assert "ə" in weak

    def test_time_accumulates_across_exercises(self, db, user_id, phoneme_results):
        get_or_create_profile(db, user_id)
        db.commit()

        post_exercise_hook(db, user_id, phoneme_results, 30, 75.0)
        post_exercise_hook(db, user_id, phoneme_results, 45, 75.0)

        profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
        assert profile.time_spent_total_secs == 75
