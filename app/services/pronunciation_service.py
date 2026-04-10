"""
Pronunciation Scoring Service — Pod 2 integration (updated).

Key improvements over previous version:
- IPA extraction via espeak-ng / epitran (no LLM cost for IPA)
- Mistake extraction via difflib (no LLM cost for mistakes)
- Only tips generation still uses LLM (~120 tokens/call)
- Token-level Levenshtein for more accurate phoneme scoring
- overall_score = phoneme_score * 0.7 + fluency_score * 100 * 0.3
"""

import difflib
import json
import logging
import re
import subprocess
from typing import Any

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# ── Valid IPA phoneme set ─────────────────────────────────────────────────────
VALID_IPA: set[str] = {
    "p",
    "b",
    "t",
    "d",
    "k",
    "g",
    "f",
    "v",
    "θ",
    "ð",
    "s",
    "z",
    "ʃ",
    "ʒ",
    "h",
    "m",
    "n",
    "ŋ",
    "l",
    "r",
    "j",
    "w",
    "i",
    "ɪ",
    "e",
    "ɛ",
    "æ",
    "ɑ",
    "ɔ",
    "oʊ",
    "u",
    "ʊ",
    "ə",
    "ʌ",
    "aɪ",
    "aʊ",
    "ɔɪ",
    "tʃ",
    "dʒ",
    "ɾ",
}

_DIGRAPHS: list[str] = sorted(
    [ph for ph in VALID_IPA if len(ph) > 1],
    key=len,
    reverse=True,
)

_DISFLUENCY_MARKERS = ("um", "uh", "erm", "like", "...", "--")


# ── IPA utilities ─────────────────────────────────────────────────────────────


def split_ipa(ipa: str) -> list[str]:
    """
    Tokenise an IPA string into a list of phoneme tokens.
    Multi-character digraphs are kept together (e.g. 'tʃ', 'aɪ').
    Stress markers and spaces are dropped.
    """
    tokens: list[str] = []
    i = 0
    while i < len(ipa):
        matched = False
        for dg in _DIGRAPHS:
            if ipa[i : i + len(dg)] == dg:
                tokens.append(dg)
                i += len(dg)
                matched = True
                break
        if not matched:
            ch = ipa[i]
            if ch not in ("ˈ", "ˌ", " "):
                tokens.append(ch)
            i += 1
    return tokens


def normalize_ipa(ipa: str) -> str:
    """Lowercase and strip bracketing characters."""
    if not ipa:
        return ""
    ipa = ipa.lower()
    ipa = re.sub(r"[/\[\]]", "", ipa)
    return ipa.strip()


def levenshtein_tokens(a: list[str], b: list[str]) -> int:
    """Standard Levenshtein edit distance on token lists."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for tok_a in a:
        curr = [prev[0] + 1]
        for j, tok_b in enumerate(b, 1):
            cost = 0 if tok_a == tok_b else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def clean_phonemes(phoneme_details: list[dict]) -> list[dict]:
    """Remove entries whose 'phoneme' key is not in VALID_IPA."""
    return [item for item in phoneme_details if item.get("phoneme") in VALID_IPA]


# ── IPA extraction (espeak-ng → epitran, no LLM cost) ────────────────────────


def _ipa_via_espeak(text: str) -> str:
    """Use espeak-ng subprocess to convert text → IPA."""
    try:
        result = subprocess.run(  # noqa: S603
            ["espeak-ng", "-q", "--ipa", "-v", "en-us", text],  # noqa: S607
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            ipa = " ".join(result.stdout.strip().splitlines())
            return ipa.strip()
    except FileNotFoundError:
        logger.warning("espeak-ng not found, falling back to epitran.")
    except subprocess.TimeoutExpired:
        logger.warning("espeak-ng timed out for input: %s", text[:50])
    except Exception as exc:
        logger.error("espeak-ng error: %s", exc)
    return ""


def _ipa_via_epitran(text: str) -> str:
    """Use epitran as fallback IPA converter."""
    try:
        import epitran

        epi = epitran.Epitran("eng-Latn")
        return epi.transliterate(text).strip()
    except ImportError:
        logger.warning("epitran not installed. pip install epitran to enable fallback.")
    except Exception as exc:
        logger.error("epitran error: %s", exc)
    return ""


def extract_ipa(text: str) -> str:
    """
    Public IPA extraction entry point.
    Priority: espeak-ng → epitran → empty string (no LLM).
    """
    if not text:
        return ""
    ipa = _ipa_via_espeak(text)
    if ipa:
        return ipa
    ipa = _ipa_via_epitran(text)
    if ipa:
        return ipa
    logger.error("Both espeak-ng and epitran failed for: %s", text[:80])
    return ""


# ── Fluency scoring ───────────────────────────────────────────────────────────


def compute_fluency(transcript: str) -> float:
    """Simple disfluency-based fluency score in [0, 1]."""
    if not transcript:
        return 0.0
    lower = transcript.lower()
    penalties = sum(lower.count(m) for m in _DISFLUENCY_MARKERS)
    return round(max(0.5, 1.0 - penalties * 0.1), 3)


# ── Mistake extraction (difflib, no LLM cost) ─────────────────────────────────


def extract_mistakes(reference: str, transcript: str) -> list[dict]:
    """
    Word-level diff using difflib.
    Returns list of {expected, spoken, type} dicts.
    Types: 'missing' | 'wrong' | 'extra'
    """
    if not reference or not transcript:
        return []

    ref_words = reference.lower().split()
    spoken_words = transcript.lower().split()
    matcher = difflib.SequenceMatcher(None, ref_words, spoken_words, autojunk=False)
    mistakes: list[dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        elif tag == "replace":
            ref_chunk = ref_words[i1:i2]
            spk_chunk = spoken_words[j1:j2]
            for exp, spk in zip(ref_chunk, spk_chunk, strict=False):
                mistakes.append({"expected": exp, "spoken": spk, "type": "wrong"})
            for exp in ref_chunk[len(spk_chunk) :]:
                mistakes.append({"expected": exp, "spoken": "", "type": "missing"})
            for spk in spk_chunk[len(ref_chunk) :]:
                mistakes.append({"expected": "", "spoken": spk, "type": "extra"})
        elif tag == "delete":
            for exp in ref_words[i1:i2]:
                mistakes.append({"expected": exp, "spoken": "", "type": "missing"})
        elif tag == "insert":
            for spk in spoken_words[j1:j2]:
                mistakes.append({"expected": "", "spoken": spk, "type": "extra"})

    return mistakes


# ── Tip generation (only LLM call remaining) ──────────────────────────────────


def gpt_generate_tips(
    reference_text: str,
    transcript: str,
    mistakes: list[dict],
) -> list[str]:
    """
    Generate 2-3 actionable pronunciation tips via LangChain GPT-4o-mini.
    This is the only remaining LLM call.
    """
    if not mistakes:
        return ["Great job! Keep practising for fluency."]

    prompt = (
        f"Pronunciation mistakes:\n"
        f"Ref: {reference_text}\n"
        f"Spoken: {transcript}\n"
        f"Errors: {json.dumps(mistakes)}\n\n"
        "Give 2-3 concise actionable tips targeting these mistakes.\n"
        "Return ONLY a JSON array of strings. No explanation."
    )

    try:
        from app.services.llm_client import get_chat_llm

        llm = get_chat_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return ["Focus on the mispronounced words and repeat slowly."]
    except Exception as exc:
        logger.error("gpt_generate_tips failed: %s", exc)
        return ["Focus on the mispronounced words and repeat slowly."]


# ── Main scoring entry point ──────────────────────────────────────────────────


def compute_pronunciation_scores(
    reference_text: str,
    transcript: str,
) -> dict[str, Any]:
    """
    Full pronunciation scoring pipeline.

    Returns:
        reference_text, transcript, ref_ipa, user_ipa,
        phoneme_score (0-100), fluency_score (0-1), overall_score (0-100),
        mistakes, tips, phoneme_details, strong_phonemes, weak_phonemes
    """
    # Step 1: IPA extraction (no LLM)
    ref_ipa = normalize_ipa(extract_ipa(reference_text))
    user_ipa = normalize_ipa(extract_ipa(transcript))

    # Step 2: Phoneme-level comparison
    phoneme_details: list[dict] = []
    strong_phonemes: list[dict] = []
    weak_phonemes: list[dict] = []

    if ref_ipa and user_ipa:
        ref_tokens = split_ipa(ref_ipa)
        user_tokens = split_ipa(user_ipa)
        min_len = min(len(ref_tokens), len(user_tokens))

        for i in range(min_len):
            ref_ph = ref_tokens[i]
            user_ph = user_tokens[i]
            correct = ref_ph == user_ph
            accuracy = 100.0 if correct else 0.0
            entry = {
                "phoneme": ref_ph,
                "total_attempts": 1,
                "correct_attempts": 1 if correct else 0,
                "accuracy": accuracy,
            }
            phoneme_details.append(entry)
            if accuracy >= 70:
                strong_phonemes.append({"phoneme": ref_ph})
            elif accuracy < 50:
                weak_phonemes.append({"phoneme": ref_ph})

        for i in range(min_len, len(ref_tokens)):
            ref_ph = ref_tokens[i]
            phoneme_details.append(
                {
                    "phoneme": ref_ph,
                    "total_attempts": 1,
                    "correct_attempts": 0,
                    "accuracy": 0.0,
                }
            )
            weak_phonemes.append({"phoneme": ref_ph})

    # Step 3: Filter invalid IPA
    phoneme_details = clean_phonemes(phoneme_details)
    strong_phonemes = clean_phonemes(strong_phonemes)
    weak_phonemes = clean_phonemes(weak_phonemes)

    # Step 4: Phoneme score (token-level Levenshtein)
    if not ref_ipa or not user_ipa:
        phoneme_score = 0.0
    else:
        ref_tokens_full = split_ipa(ref_ipa)
        user_tokens_full = split_ipa(user_ipa)
        dist = levenshtein_tokens(ref_tokens_full, user_tokens_full)
        max_len = max(len(ref_tokens_full), len(user_tokens_full), 1)
        phoneme_score = round(max(0.0, 1.0 - dist / max_len) * 100, 2)

    # Step 5: Fluency
    fluency_score = compute_fluency(transcript)

    # Step 6: Mistakes (difflib, no LLM)
    mistakes = extract_mistakes(reference_text, transcript)

    # Step 7: Tips (only LLM call)
    tips = gpt_generate_tips(reference_text, transcript, mistakes)

    # Step 8: Overall score
    overall_score = round(phoneme_score * 0.7 + fluency_score * 100 * 0.3, 2)

    return {
        "reference_text": reference_text,
        "transcript": transcript,
        "ref_ipa": ref_ipa,
        "user_ipa": user_ipa,
        "phoneme_score": phoneme_score,
        "fluency_score": fluency_score,
        "overall_score": overall_score,
        "mistakes": mistakes,
        "tips": tips,
        "phoneme_details": phoneme_details,
        "strong_phonemes": strong_phonemes,
        "weak_phonemes": weak_phonemes,
    }
