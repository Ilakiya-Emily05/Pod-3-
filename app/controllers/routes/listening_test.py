import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.models.listening1 import ListeningSession
from app.services.listening_question import evaluate_answers_batch
from app.services.transcription import transcribe_audio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])

settings = get_settings()


@router.post("/evaluate", summary="Evaluate all 3 spoken answers for a listening session")
async def evaluate_listening_answers(
    session_id: str = Form(..., description="session_id from /module response"),
    audio_1: UploadFile = File(...),
    audio_2: UploadFile = File(...),
    audio_3: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ── 1. Fetch session from DB ──────────────────────────────────────────────
    session = db.query(ListeningSession).filter(ListeningSession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found. Call GET /listening/module first.",
        )

    passage = session.passage
    questions = session.questions  # list of {id, question, difficulty}

    if not questions or len(questions) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session has {len(questions or [])} questions, expected 3.",
        )

    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_files = []

    try:
        # ── 2. Transcribe all 3 audio files ───────────────────────────────────
        audio_files = [audio_1, audio_2, audio_3]
        answers = []

        for i, audio_file in enumerate(audio_files):
            q = questions[i]
            suffix = Path(audio_file.filename or "audio.bin").suffix or ".bin"
            temp_path = temp_dir / f"{session_id}_q{i + 1}{suffix}"
            temp_files.append(temp_path)

            temp_path.write_bytes(await audio_file.read())
            transcript = transcribe_audio(temp_path)

            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Transcription failed for question {i + 1}. Check audio quality.",
                )

            logger.info("Q%d transcript: %s", i + 1, transcript[:80])
            answers.append(
                {
                    "question_id": q["id"],
                    "question": q["question"],
                    "answer": transcript,
                }
            )

        # ── 3. Batch evaluate in one LLM call ─────────────────────────────────
        results = evaluate_answers_batch(passage=passage, answers=answers)
        total_score = round(sum(r.get("score", 0) for r in results) / len(results), 2)

        # ── 4. Update session in DB ───────────────────────────────────────────
        session.user_transcript = json.dumps([a["answer"] for a in answers])
        session.similarity_score = total_score
        db.commit()

        return {
            "session_id": session_id,
            "total_score": total_score,
            "results": [
                {
                    "question_id": r.get("question_id"),
                    "question": answers[i]["question"],
                    "transcript": answers[i]["answer"],
                    "correct": r.get("correct", False),
                    "score": r.get("score", 0),
                    "feedback": r.get("feedback", ""),
                }
                for i, r in enumerate(results)
            ],
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("evaluate_listening_answers failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed due to an internal error.",
        )
    finally:
        for path in temp_files:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
