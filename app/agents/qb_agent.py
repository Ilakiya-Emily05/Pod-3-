import logging
import uuid

from app.services.listening1 import generate_passage, generate_questions_from_passage
from app.services.pronun_question import generate_pronunciation_questions
from app.services.tts_service import text_to_speech

logger = logging.getLogger(__name__)


def score_to_difficulty(score: float) -> str:
    if score < 40:
        return "easy"
    elif score <= 70:
        return "medium"
    return "hard"


# -----------------------------
# Main function to generate full module
# -----------------------------
def generate_agent_module(score: float) -> dict:
    """
    Generates a full learning module based on the user's pronunciation score.

    Returns:
        {
            "session_id":               str (UUID),
            "difficulty":               str,
            "passage":                  str,
            "audio_url":                str,
            "listening_questions":      list[dict],
            "pronunciation_questions":  list[dict],
        }
    """
    session_id = str(uuid.uuid4())
    difficulty = score_to_difficulty(score)

    try:
        passage = generate_passage(difficulty=difficulty)

        audio_filename = f"agent_{uuid.uuid4().hex}.mp3"
        audio_url = text_to_speech(passage, audio_filename) or "/static/audio/fallback_passage.mp3"

        listening_questions = generate_questions_from_passage(
            passage, num_questions=3, difficulty=difficulty
        )
        pronunciation_questions = generate_pronunciation_questions(passage, num_questions=2)

        return {
            "session_id": session_id,
            "difficulty": difficulty,
            "passage": passage,
            "audio_url": audio_url,
            "listening_questions": listening_questions,
            "pronunciation_questions": pronunciation_questions,
        }

    except Exception as exc:
        logger.exception("generate_agent_module failed: %s", exc)
        fallback = "The sun rises in the east every morning."
        return {
            "session_id": session_id,
            "difficulty": difficulty,
            "passage": fallback,
            "audio_url": "/static/audio/fallback_passage.mp3",
            "listening_questions": [
                {"id": 1, "difficulty": difficulty, "question": "What was described?"}
            ],
            "pronunciation_questions": [{"difficulty": difficulty, "question": fallback}],
        }
