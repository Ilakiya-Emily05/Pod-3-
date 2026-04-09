# app/routes/listening_audio_eval_route.py

import json
import os

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from openai import OpenAI
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.listening_model import ListeningAttempt

router = APIRouter(prefix="/listening", tags=["Listening Evaluation"])

client = OpenAI()


def get_whisper_model(request: Request):
    return request.app.state.whisper_model


# ---------------------------------------------
# LLM-BASED SEMANTIC EVALUATION (GPT-4o-mini)
# ---------------------------------------------
def evaluate_semantic_score(expected: str, transcript: str):
    prompt = f"""
You are evaluating a student's LISTENING COMPREHENSION.

PASSAGE / EXPECTED ANSWER:
\"\"\"{expected}\"\"\"

USER'S TRANSCRIBED ANSWER:
\"\"\"{transcript}\"\"\"

Evaluate ONLY comprehension accuracy.

Return STRICT JSON in this format:
{{
  "relevance": <0-100>,
  "correctness": <0-100>,
  "feedback": "<short explanation>"
}}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )

    # Safe JSON parsing
    try:
        data = json.loads(resp.choices[0].message.content)
        return data
    except Exception:
        return {"relevance": 0, "correctness": 0, "feedback": "Model returned invalid JSON"}


# ---------------------------------------------
# MAIN LISTENING AUDIO EVALUATION ROUTE
# ---------------------------------------------
@router.post("/submit-audio")
async def evaluate_listening_audio(
    question_text: str = Form(...),
    file: UploadFile = None,
    model=Depends(get_whisper_model),
    db: Session = Depends(get_db),
):
    if file is None:
        return JSONResponse({"error": "No audio file uploaded"}, status_code=400)

    # Save temporarily
    temp_path = f"temp_{file.filename}"
    audio_filename = f"user_{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Whisper transcription
    result = model.transcribe(temp_path)
    user_transcript = result["text"].strip()

    expected_text = question_text.strip()

    # LLM scoring
    semantic = evaluate_semantic_score(expected_text, user_transcript)

    # Store in DB
    attempt = ListeningAttempt(
        passage=expected_text,
        questions=[{"question": expected_text}],
        user_transcript=user_transcript,
        similarity_score=semantic["correctness"],  # store correctness
        audio_filename=audio_filename,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Delete temp file
    try:
        os.remove(temp_path)
    except:
        pass

    # Response
    return {
        "expected_answer": expected_text,
        "user_transcript": user_transcript,
        "relevance": semantic["relevance"],
        "correctness": semantic["correctness"],
        "feedback": semantic["feedback"],
    }
