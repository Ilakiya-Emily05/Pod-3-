# app/routes/listening_route.py
from fastapi import APIRouter
from app.services.listening_service import generate_listening_module

router = APIRouter(
    prefix="/listening",
    tags=["Listening Module"]
)

@router.get("/module")
async def get_listening_module():
    """
    Returns a listening passage, TTS audio URL, and dynamically generated questions.
    """
    try:
        result = generate_listening_module()
        return result
    except Exception as e:
        
        # Fallback
        fallback_passage = "Please repeat the sentence: The sun is bright today."
        return {
            "passage": fallback_passage,
            "audio_url": "/static/audio/fallback_passage.mp3",
            "listening_questions": [{"id": 1, "text": fallback_passage}]
        }