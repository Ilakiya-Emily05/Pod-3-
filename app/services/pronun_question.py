import json
import logging
import re

from langchain_core.messages import HumanMessage

from app.services.llm_client import get_chat_llm

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = (
    "Generate {num_questions} English sentence(s) for pronunciation practice "
    "at the {difficulty} level.\n\n"
    "Return ONLY a JSON array where each item has:\n"
    '[{{"difficulty": "{difficulty}", "question": "<sentence>"}}]\n\n'
    "No explanation, no markdown — valid JSON only."
)

_FALLBACK = {"difficulty": "easy", "question": "The sun is bright today."}


def score_to_difficulty(score: float) -> str:
    if score < 40:
        return "easy"
    elif score <= 70:
        return "medium"
    return "hard"


class PronunciationQuestionsService:
    """Generate pronunciation exercises based on score."""

    @staticmethod
    def generate_questions(score: float, num_questions: int = 2) -> list[dict]:
        """
        Generate `num_questions` pronunciation sentences calibrated
        to the user's current score.
        """
        difficulty = score_to_difficulty(score)
        prompt = _PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            difficulty=difficulty,
        )
        llm = get_chat_llm(temperature=0.7)
        try:
            response = llm.invoke(
                [HumanMessage(content=prompt)],
                config={"run_name": "generate_pronunciation_questions"},
            )
            raw = response.content.strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
                for q in questions:
                    q.setdefault("difficulty", difficulty)
                return questions
        except Exception as exc:
            logger.error("PronunciationQuestionsService.generate_questions failed: %s", exc)

        return [dict(_FALLBACK, difficulty=difficulty)] * num_questions


# Module-level function used by qb_agent
def generate_pronunciation_questions(passage: str, num_questions: int = 2) -> list[dict]:
    """
    Generate pronunciation exercises inspired by a specific passage.
    Difficulty defaults to 'medium' since no score is available.
    """
    prompt = (
        f"Based on the following passage, generate {num_questions} short sentences "
        "for pronunciation practice at medium difficulty.\n\n"
        f"PASSAGE:\n{passage}\n\n"
        "Return ONLY a JSON array:\n"
        '  [{"difficulty": "medium", "question": "<sentence>"}]\n'
        "No other text."
    )
    llm = get_chat_llm(temperature=0.7)
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": "generate_pronun_questions_from_passage"},
        )
        raw = response.content.strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as exc:
        logger.error("generate_pronunciation_questions failed: %s", exc)
    return [{"difficulty": "medium", "question": "Please repeat: The sun is bright today."}]
