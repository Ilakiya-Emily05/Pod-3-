"""
Pronunciation Analyzer — Sprint 2 Task 2
Calls Pod 2's phoneme engine with a 30-second timeout.
If it times out or fails, returns graceful empty response.
"""
import asyncio
from functools import partial


async def analyze_pronunciation(
    reference_text: str,
    transcript: str,
) -> dict:
    empty = {
        "phoneme_score": None,
        "fluency_score": None,
        "mistakes": [],
        "tips": [],
    
    }

    if not transcript or not reference_text:
        return empty

    try:
        from app.services.pronunciation_service import compute_pronunciation_scores

        loop = asyncio.get_event_loop()
        fn = partial(compute_pronunciation_scores, reference_text, transcript)

        # 30 second timeout — if Pod 2 engine hangs, return empty gracefully
        result = await asyncio.wait_for(
            loop.run_in_executor(None, fn),
            timeout=30.0
        )

        if not isinstance(result, dict):
            return empty

        return {
            "phoneme_score": int(result["phoneme_score"]) if isinstance(result.get("phoneme_score"), (int, float)) else None,
            "fluency_score": float(result["fluency_score"]) if isinstance(result.get("fluency_score"), (int, float)) else None,
            "mistakes": result["mistakes"] if isinstance(result.get("mistakes"), list) else [],
            "tips": result["tips"] if isinstance(result.get("tips"), list) else [],
            "ref_ipa": str(result["ref_ipa"]) if result.get("ref_ipa") else None,
            "user_ipa": str(result["user_ipa"]) if result.get("user_ipa") else None,
        }

    except asyncio.TimeoutError:
        print("Pronunciation analysis timed out after 30s")
        return empty
    except Exception as e:
        print(f"Pronunciation analysis failed: {type(e).__name__}: {e}")
        return empty