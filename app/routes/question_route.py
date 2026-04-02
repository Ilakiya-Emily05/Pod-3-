# routes/question_route.py
from fastapi import APIRouter, Query
from app.services.question_service import generate_pronunciation_question

router = APIRouter(prefix="/question", tags=["question"])

@router.get("/next")
def get_next_question_route(score: float = Query(..., ge=0, le=100)):
    """
    Generate next pronunciation question dynamically based on user score.
    """
    questions = generate_pronunciation_question(score, num_questions=1)
    question = questions[0] if questions else {"difficulty": "easy", "question": "Practice reading aloud."}

    return {
        "difficulty": question["difficulty"],
        "question_text": question["question"],
        
    }