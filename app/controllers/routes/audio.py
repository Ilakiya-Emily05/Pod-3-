import logging
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.repositories.pronunciation import get_or_create_profile
from app.services.audio import convert_to_wav
from app.services.post_ex_service import post_exercise_hook
from app.services.scoring import compute_pronunciation_scores
from app.services.transcription import transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Pronunciation"])

settings = get_settings()


@router.post("/analyze", summary="Analyse pronunciation audio")
async def analyze_audio(
    file: UploadFile,
    user_id: uuid.UUID = Query(..., description="Caller-supplied UUID user ID"),
    db: Session = Depends(get_db),
    # reference_text is now optional — uses stored question if not passed
    reference_text: str | None = Query(
        None, description="The sentence the user should have spoken (optional if /next was called)"
    ),
):
    """
    Pipeline:
      1. Save uploaded audio to disk.
      2. Convert to WAV.
      3. Transcribe via OpenAI Whisper.
      4. Score pronunciation (IPA comparison, fluency, mistakes, tips).
      5. Persist phoneme stats and profile.
      6. Return full analysis result with a UUID request_id.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    original_suffix = Path(file.filename or "audio.bin").suffix or ".bin"
    temp_path = temp_dir / f"{request_id}{original_suffix}"
    wav_path: Path | None = None

    try:
        # ── 1. Ensure profile exists ──────────────────────────────────────────
        profile = get_or_create_profile(db, user_id)

        # ── 2. Resolve reference text ─────────────────────────────────────────
        ref_text = reference_text or profile.current_question
        if not ref_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No reference text provided and no question stored. Call GET /question/next first.",
            )

        # ── 3. Save upload ────────────────────────────────────────────────────
        contents = await file.read()
        temp_path.write_bytes(contents)
        logger.debug("[%s] Saved upload to %s (%d bytes)", request_id, temp_path, len(contents))

        # ── 4. Convert to WAV ─────────────────────────────────────────────────
        audio_format = temp_path.suffix.lstrip(".").lower()
        wav_path = convert_to_wav(temp_path, audio_format)

        # ── 5. Transcribe ─────────────────────────────────────────────────────
        transcript = transcribe_audio(wav_path)
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio transcription returned empty result. Check audio quality.",
            )

        # ── 6. Score ──────────────────────────────────────────────────────────
        result = compute_pronunciation_scores(ref_text, transcript)

        phoneme_score: float = result["phoneme_score"]
        fluency_score: float = result["fluency_score"]
        overall_score: float = result["overall_score"]
        phoneme_details: list = result["phoneme_details"]
        weak_phonemes: list = result["weak_phonemes"]
        strong_phonemes: list = result["strong_phonemes"]
        mistakes: list = result["mistakes"]
        tips: list = result["tips"]

        # ── 7. Build phoneme results for DB ───────────────────────────────────
        phoneme_results = [
            {
                "phoneme": d["phoneme"],
                "correct": d["correct_attempts"] > 0,
                "accuracy": d["accuracy"],
                "total_attempts": d["total_attempts"],
                "correct_attempts": d["correct_attempts"],
            }
            for d in phoneme_details
            if d.get("phoneme")
        ]

        # ── 8. Run post-exercise pipeline ─────────────────────────────────────
        elapsed_secs = int(time.time() - start_time)
        post_exercise_hook(
            db=db,
            user_id=user_id,
            phoneme_results=phoneme_results,
            time_spent_secs=elapsed_secs,
            current_score=overall_score,
        )

        # ── 9. Clear stored question after use ────────────────────────────────
        profile.current_question = None
        db.commit()

        logger.info(
            "[%s] Analysis complete for user_id=%s: phoneme_score=%.1f overall=%.1f",
            request_id,
            user_id,
            phoneme_score,
            overall_score,
        )

        return {
            "request_id": request_id,
            "user_id": user_id,
            "reference_text": ref_text,
            "transcript": transcript,
            "ref_ipa": result["ref_ipa"],
            "user_ipa": result["user_ipa"],
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "overall_score": overall_score,
            "weak_phonemes": weak_phonemes,
            "strong_phonemes": strong_phonemes,
            "mistakes": mistakes,
            "tips": tips,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("[%s] analyze_audio failed: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed due to an internal error.",
        ) from exc
    finally:
        for path in (temp_path, wav_path):
            if path and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
