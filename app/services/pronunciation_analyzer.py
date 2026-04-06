"""
Pronunciation Analyzer — Sprint 2 Task 2

Async wrapper around Pod 2's phoneme engine.
Calls compute_pronunciation_scores in a thread pool with a 30-second timeout.
If it times out or fails, returns a graceful empty response.
"""
import asyncio
import logging
from functools import partial

logger = logging.getLogger(__name__)


async def analyze_pronunciation(
    reference_text: str,
    transcript: str,
) -> dict:
    """
    Analyze pronunciation by comparing reference text against user transcript.

    Args:
        reference_text: The original question text (expected speech).
        transcript: What the user actually said (from Whisper).

    Returns:
        dict with phoneme_score, fluency_score, mistakes, tips.
    """
    empty: dict = {
        "phoneme_score": None,
        "fluency_score": None,
        "mistakes": [],
        "tips": [],
    }

    if not transcript or not reference_text:
        return empty

    try:
        from app.services.pronunciation_service import compute_pronunciation_scores  # noqa: PLC0415

        loop = asyncio.get_event_loop()
        fn = partial(compute_pronunciation_scores, reference_text, transcript)

        result = await asyncio.wait_for(
            loop.run_in_executor(None, fn),
            timeout=30.0,
        )

        if not isinstance(result, dict):
            return empty

        return {
            "phoneme_score": int(result["phoneme_score"])
            if isinstance(result.get("phoneme_score"), (int, float))
            else None,
            "fluency_score": float(result["fluency_score"])
            if isinstance(result.get("fluency_score"), (int, float))
            else None,
            "mistakes": result["mistakes"]
            if isinstance(result.get("mistakes"), list)
            else [],
            "tips": result["tips"]
            if isinstance(result.get("tips"), list)
            else [],
        }

    except asyncio.TimeoutError:
        logger.warning("Pronunciation analysis timed out after 30s")
        return empty
    except Exception as e:  # noqa: BLE001
        logger.exception("Pronunciation analysis failed: %s: %s", type(e).__name__, e)
        return empty