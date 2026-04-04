
# pronunciation_engine.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# -------------------------------
# GPT helpers: IPA extraction
# -------------------------------
def gpt_extract_ipa(text: str) -> str:
    prompt = f"""
Convert the following English text to IPA only.
Rules:
- Output ONLY IPA.
- No brackets or slashes.
- No explanation.

TEXT:
{text}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0
        )
        ipa = res.choices[0].message.content.strip()
        ipa = ipa.replace("/", "").replace("[", "").replace("]", "")
        return ipa
    except Exception as e:
       
        return ""


# -------------------------------
# GPT mistake extraction
# -------------------------------
def gpt_extract_mistakes(reference: str, transcript: str):
    """
    Extract pronunciation / word-level mistakes.
    Output strictly JSON list of objects.
    """
    prompt = f"""
Compare the reference sentence and the spoken transcript.

REFERENCE:
{reference}

TRANSCRIPT:
{transcript}

Return ONLY a JSON array named "mistakes".
Each element must be:
{{
  "expected": "<word from reference>",
  "spoken": "<word from user>",
  "type": "missing|wrong|extra"
}}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300
        )

        content = res.choices[0].message.content.strip()
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if not match:
            return []

        return json.loads(match.group(0))
    except Exception as e:
       
        return []


# -------------------------------
# NEW: GPT targeted pronunciation tips
# -------------------------------
def gpt_generate_tips(reference_text, transcript, mistakes):
    """
    Generate 2–3 short pronunciation tips based on actual mistakes.
    Very cheap GPT call (<30 tokens).
    """
    prompt = f"""
The user read a sentence aloud and made the following pronunciation mistakes:

REFERENCE: {reference_text}
TRANSCRIPT: {transcript}

MISTAKES:
{json.dumps(mistakes, indent=2)}

Give 2–3 short, actionable pronunciation tips directly targeting ONLY these mistakes.
No grammar tips. No generic praise.
Return ONLY a JSON list of strings.
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120
        )

        content = res.choices[0].message.content.strip()
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if not match:
            return ["Focus on improving the mispronounced words."]

        return json.loads(match.group(0))

    except:
        return ["Focus on improving the mispronounced words."]


# -------------------------------
# IPA normalization
# -------------------------------
def normalize_ipa(ipa: str) -> str:
    if not ipa:
        return ""
    ipa = ipa.lower()
    ipa = re.sub(r"[^a-zɑ-ɒɔəɜɪʊʌæθðŋʃʒɹɾʔːˑˈˌ]+", "", ipa)
    return ipa


# -------------------------------
# Levenshtein Distance
# -------------------------------
def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + cost))
        prev = curr
    return prev[-1]


# -------------------------------
# Fluency scoring
# -------------------------------
def compute_fluency(transcript: str) -> float:
    if not transcript:
        return 0.0
    penalties = 0
    fillers = ["um", "uh", "erm", "like", "...", "--"]

    for f in fillers:
        if f in transcript.lower():
            penalties += 1

    # Limit penalty to 0.5
    score = 1.0 - min(0.5, penalties * 0.1)
    return round(score, 3)


# -------------------------------
# Main scoring function
# -------------------------------
def compute_pronunciation_scores(reference_text: str, transcript: str):
    try:
        # IPA extraction
        ref_ipa = normalize_ipa(gpt_extract_ipa(reference_text))
        user_ipa = normalize_ipa(gpt_extract_ipa(transcript))

        if not ref_ipa or not user_ipa:
            phoneme_score = 0
        else:
            dist = levenshtein(ref_ipa, user_ipa)
            max_len = max(len(ref_ipa), len(user_ipa))
            similarity = 1 - (dist / max_len)
            phoneme_score = round(max(similarity, 0) * 100)

        fluency_score = compute_fluency(transcript)
        mistakes = gpt_extract_mistakes(reference_text, transcript)
        if mistakes:
            tips = gpt_generate_tips(reference_text, transcript, mistakes)
        elif phoneme_score < 60:
            tips = [
        "Try to speak more clearly and match the expected pronunciation.",
        "Practice speaking the answer aloud before recording.",
        "Focus on enunciating each word carefully."
        ]
        else:
            tips = ["Great job! Your pronunciation is improving."]

        return {
            "reference_text": reference_text,
            "transcript": transcript,
            "ref_ipa": str(ref_ipa) if ref_ipa else "",
            "user_ipa": str(user_ipa) if user_ipa else "",
            "phoneme_score": int(phoneme_score),
            "fluency_score": float(fluency_score),
            "mistakes": mistakes if isinstance(mistakes, list) else [],
            "tips": tips if isinstance(tips, list) else [],
        }
    except Exception as e:
        return {
            "reference_text": reference_text,
            "transcript": transcript,
            "ref_ipa": "",
            "user_ipa": "",
            "phoneme_score": 0,
            "fluency_score": 0.0,
            "mistakes": [],
            "tips": ["Pronunciation analysis unavailable."],
        }