"""
Pronunciation Analyzer

Async wrapper around Pod 2's updated scoring_service.
Runs CPU-bound analysis in a thread pool with a 30-second timeout.
Returns graceful empty response on failure.
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
        dict with phoneme_score, fluency_score, overall_score,
        mistakes, tips, strong_phonemes, weak_phonemes.
    """
    empty: dict = {
        "phoneme_score": None,
        "fluency_score": None,
        "overall_score": None,
        "mistakes": [],
        "tips": [],
        "strong_phonemes": [],
        "weak_phonemes": [],
    }

    if not transcript or not reference_text:
        return empty

    try:
        from app.services.pronunciation_service import compute_pronunciation_scores

        loop = asyncio.get_event_loop()
        fn = partial(compute_pronunciation_scores, reference_text, transcript)

        result = await asyncio.wait_for(
            loop.run_in_executor(None, fn),
            timeout=30.0,
        )

        if not isinstance(result, dict):
            return empty

        return {
            "phoneme_score": float(result["phoneme_score"])
            if isinstance(result.get("phoneme_score"), (int, float))
            else None,
            "fluency_score": float(result["fluency_score"])
            if isinstance(result.get("fluency_score"), (int, float))
            else None,
            "overall_score": float(result["overall_score"])
            if isinstance(result.get("overall_score"), (int, float))
            else None,
            "mistakes": result["mistakes"] if isinstance(result.get("mistakes"), list) else [],
            "tips": result["tips"] if isinstance(result.get("tips"), list) else [],
            "strong_phonemes": result["strong_phonemes"]
            if isinstance(result.get("strong_phonemes"), list)
            else [],
            "weak_phonemes": result["weak_phonemes"]
            if isinstance(result.get("weak_phonemes"), list)
            else [],
        }

    except TimeoutError:
        logger.warning("Pronunciation analysis timed out after 30s")
        return empty
    except Exception as e:
        logger.exception("Pronunciation analysis failed: %s: %s", type(e).__name__, e)
        return empty
