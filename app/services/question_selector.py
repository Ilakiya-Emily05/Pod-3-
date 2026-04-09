# services/question_selector.py

import secrets

from app.data.questions import QUESTIONS


class QuestionGenerationService:
    """Generate questions based on a normalized score.

    Uses a static question bank (QUESTIONS) as fallback.
    """

    def get_difficulty(self, score: float) -> str:
        """Map a normalized score (0.0-1.0) to a difficulty level."""
        if score < 0.20:
            return "basic"
        if score < 0.40:
            return "easy"
        if score < 0.60:
            return "intermediate"
        if score < 0.80:
            return "advanced"
        return "very_difficult"

    def generate_question(self, score: float) -> dict[str, str]:
        """Return a dict with difficulty + question text."""
        normalized = score / 100.0
        difficulty = self.get_difficulty(normalized)
        question_list = QUESTIONS.get(difficulty, [])
        question_data = (
            secrets.choice(question_list) if question_list else {"text": "Practice reading aloud."}
        )
        return {"difficulty": difficulty, "question": question_data["text"]}
