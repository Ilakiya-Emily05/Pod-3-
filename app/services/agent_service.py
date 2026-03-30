# app/services/agent_service.py

import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

from app.prompts.question_prompt import PROMPT

# Load env
load_dotenv()

# Initialize client here directly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_json_safe(text: str):
    """
    Extracts FIRST valid JSON object or array from the LLM response.
    Useful because LLM may return extra text before/after JSON.
    """
    patterns = [
        r"(\{.*\})",
        r"(\[.*\])"
    ]
    for p in patterns:
        match = re.search(p, text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None


def generate_passage(difficulty: str) -> str:
    prompt = (
        f"Write a short {difficulty} English passage for listening comprehension "
        "practice. Keep it simple and suitable for pronunciation exercises."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return ONLY plain text. No JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=250
    )

    return response.choices[0].message.content.strip()


def generate_questions(passage: str, num_questions: int = 3) -> list:
    prompt = (
        f"Based on this passage, generate {num_questions} comprehension questions.\n"
        "Return ONLY a valid JSON array of objects like:\n"
        '[{"difficulty": "easy", "question": "..."}]\n\n'
        f"Passage:\n{passage}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    raw = response.choices[0].message.content.strip()
    parsed = extract_json_safe(raw)

    if parsed:
        return parsed

    # fallback
    return [
        {"difficulty": "easy", "question": "What is the main idea of the passage?"},
        {"difficulty": "medium", "question": "Explain the second sentence."},
        {"difficulty": "hard", "question": "Interpret the author's intent."}
    ]


def generate_pronunciation_questions(passage: str, num_questions: int = 2) -> list:
    prompt = (
        f"Extract {num_questions} short sentences suitable for pronunciation practice.\n"
        "Return ONLY JSON array:\n"
        '[{"difficulty": "easy", "question": "Repeat: ..."}]\n\n'
        f"Passage:\n{passage}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )

    raw = response.choices[0].message.content.strip()
    parsed = extract_json_safe(raw)

    if parsed:
        return parsed

    return [
        {"difficulty": "easy", "question": "Repeat: 'The sun is bright today.'"},
        {"difficulty": "medium", "question": "Repeat: 'She sells sea shells by the seashore.'"},
    ]