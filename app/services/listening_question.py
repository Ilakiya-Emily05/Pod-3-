import json
import logging
import re
import uuid

from langchain_core.messages import HumanMessage

from app.services.llm_client import get_chat_llm
from app.services.tts_service import text_to_speech

logger = logging.getLogger(__name__)

_PASSAGE_PROMPT = (
    "Generate a short {difficulty}-level English passage for listening practice. "
    "The passage should be 3-4 sentences long, natural, and engaging. "
    "Output ONLY the passage text. No title, no explanation."
)

_QUESTIONS_PROMPT = (
    "You are an English language teacher. Given the passage below, generate "
    "{num_questions} unique comprehension questions.\n\n"
    "PASSAGE:\n{passage}\n\n"
    "DIFFICULTY: {difficulty}\n\n"
    "Rules:\n"
    "- Each question must focus on a different detail or idea in the passage.\n"
    "- Questions must be clear and directly answerable from the passage.\n"
    "- Return ONLY a JSON array in this format:\n"
    '  [{{"id": 1, "difficulty": "{difficulty}", "question": "..."}}]\n'
    "No other text."
)

_BATCH_EVAL_PROMPT = (
    "You are an English language teacher evaluating a student's listening comprehension.\n\n"
    "PASSAGE:\n{passage}\n\n"
    "Evaluate each answer below. For each, return a score (0-100) and short feedback.\n\n"
    "ANSWERS:\n{answers}\n\n"
    "Return ONLY a JSON array in this exact format:\n"
    '[{{"question_id": 1, "correct": true/false, "score": 0-100, "feedback": "..."}}]\n'
    "No other text."
)


def generate_passage(difficulty: str = "medium") -> str:
    llm = get_chat_llm(temperature=0.7)
    prompt = _PASSAGE_PROMPT.format(difficulty=difficulty)
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": "generate_listening_passage"},
        )
        return response.content.strip()
    except Exception as exc:
        logger.error("generate_passage failed: %s", exc)
        return "The sun rises in the east and sets in the west."


def generate_questions_from_passage(
    passage: str,
    num_questions: int = 3,
    difficulty: str = "medium",
) -> list[dict]:
    llm = get_chat_llm(temperature=0.5)
    prompt = _QUESTIONS_PROMPT.format(
        passage=passage,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    for attempt in range(2):
        try:
            response = llm.invoke(
                [HumanMessage(content=prompt)],
                config={"run_name": "generate_listening_questions"},
            )
            raw = response.content.strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))  # ← fixed group(0)
                for idx, q in enumerate(questions):
                    q.setdefault("id", idx + 1)
                    q.setdefault("difficulty", difficulty)
                return questions
        except Exception as exc:
            logger.warning("generate_questions attempt %d failed: %s", attempt + 1, exc)

    return [
        {"id": i + 1, "difficulty": difficulty, "question": f"Question {i + 1}."}
        for i in range(num_questions)
    ]


def evaluate_answers_batch(passage: str, answers: list[dict]) -> list[dict]:
    """
    Evaluate all answers in one LLM call.
    answers = [{"question_id": 1, "question": "...", "answer": "..."}]
    """
    llm = get_chat_llm(temperature=0.0)

    # Format answers for prompt
    answers_text = "\n".join(
        f"Q{a['question_id']}: {a['question']}\nAnswer: {a['answer']}" for a in answers
    )

    prompt = _BATCH_EVAL_PROMPT.format(
        passage=passage,
        answers=answers_text,
    )

    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": "batch_evaluate_answers"},
        )
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            results = json.loads(match.group(0))
            return results
    except Exception as exc:
        logger.error("evaluate_answers_batch failed: %s", exc)

    # Fallback
    return [
        {
            "question_id": a["question_id"],
            "correct": False,
            "score": 0,
            "feedback": "Evaluation failed.",
        }
        for a in answers
    ]


def generate_listening_module(
    difficulty: str = "medium",
    num_questions: int = 3,
) -> dict:
    session_id = str(uuid.uuid4())
    try:
        passage = generate_passage(difficulty)
        questions = generate_questions_from_passage(passage, num_questions, difficulty)
        audio_filename = f"listening_{uuid.uuid4().hex}.mp3"
        audio_url = text_to_speech(passage, audio_filename)
        if not audio_url:
            audio_url = "/static/audio/fallback_passage.mp3"

        return {
            "session_id": session_id,
            "passage": passage,
            "audio_url": audio_url,
            "listening_questions": questions,
        }
    except Exception as exc:
        logger.exception("generate_listening_module failed: %s", exc)
        fallback = "Please listen carefully and answer the questions."
        return {
            "session_id": session_id,
            "passage": fallback,
            "audio_url": "/static/audio/fallback_passage.mp3",
            "listening_questions": [
                {"id": 1, "difficulty": difficulty, "question": "What did you hear?"}
            ],
        }
