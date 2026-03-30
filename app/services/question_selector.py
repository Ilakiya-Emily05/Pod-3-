# services/question_selector.py
import random
from typing import Dict
from app.data.questions import QUESTIONS

class QuestionGenerationService:
    """
    Generates questions based on a normalized score.
    Uses a static question bank (QUESTIONS) as fallback.
    """

    def get_difficulty(self, score: float) -> str:
        """
        Maps a normalized score (0.0–1.0) to a difficulty level.
        """
        if score < 0.20:
            return "basic"
        elif score < 0.40:
            return "easy"
        elif score < 0.60:
            return "intermediate"
        elif score < 0.80:
            return "advanced"
        return "very_difficult"

    def generate_question(self, score: float) -> Dict[str, str]:
        """
        Returns a dictionary with:
          - difficulty: str
          - question: str
        """
        normalized = score / 100.0
        difficulty = self.get_difficulty(normalized)
        question_list = QUESTIONS.get(difficulty, [])
        question_text = random.choice(question_list) if question_list else "Practice reading aloud."
        return {"difficulty": difficulty, "question": question_text}