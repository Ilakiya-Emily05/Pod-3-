import os
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.pronounciation_repo import save_pronunciation_result
from app.services.audio_service import convert_to_wav
from app.services.phoneme_engine import compute_pronunciation_scores
from app.services.question_service import generate_pronunciation_question
from app.services.transcription_service import transcribe_audio
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/test", tags=["pronunciation"])


@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: UploadFile,
    reference_text: str = Query(...),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Analyze uploaded audio for pronunciation.
    """
    try:
        # Save uploaded file
        os.makedirs("temp", exist_ok=True)
        temp_path = Path("temp") / file.filename
        file_content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(file_content)

        # Convert to WAV
        audio_format = temp_path.suffix.replace(".", "").lower()
        wav_path = convert_to_wav(temp_path, audio_format)

        # Transcription
        transcript = transcribe_audio(wav_path)

        # Pronunciation scoring
        result = compute_pronunciation_scores(reference_text, transcript)

        phoneme_score = result.get("phoneme_score", 0)
        fluency_score = result.get("fluency_score", 0)
        mistakes = result.get("mistakes", [])
        tips = result.get("tips", [])

        # Save in DB
        db_data = {
            "user_id": user_id,
            "transcript": transcript,
            "reference_text": reference_text,
            "pronunciation_score": phoneme_score,
            "total_mistakes": len(mistakes),
            "mistakes": mistakes,
            "improvement_tips": tips,
            "audio_path": str(wav_path),
        }
        save_pronunciation_result(db, db_data)

        # Next question
        generate_pronunciation_question(phoneme_score)

        # Final output
        return {
            "reference_text": reference_text,
            "transcript": transcript,
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "mistakes": mistakes,
            "tips": tips,
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to process audio. Ensure the file is valid and in a compatible audio format.",
        }
