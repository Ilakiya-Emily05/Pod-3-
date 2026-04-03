# agent.py
# Handles dynamic passage generation, streaming TTS, and question generation
# for both listening comprehension and pronunciation practice.

from fastapi.responses import StreamingResponse
from io import BytesIO
from gtts import gTTS
from app.services.agent_service import (
    generate_passage,
    generate_questions,
    generate_pronunciation_questions
)

# Map user score to difficulty
def score_to_difficulty(score: float) -> str:
    if score < 40:
        return "easy"
    elif 40 <= score <= 70:
        return "medium"
    else:
        return "hard"


def generate_agent_module(score: float) -> dict:
    """
    Generates:
    - Passage (from OpenAI)
    - Streaming audio of passage
    - Listening comprehension questions
    - Pronunciation questions

    Returns:
        {
            "difficulty": "...",
            "listening_questions": [...],
            "pronunciation_questions": [...],
            "audio_stream": StreamingResponse
        }
    """
    difficulty = score_to_difficulty(score)

    try:
        # 1️⃣ Generate passage
        passage = generate_passage(difficulty=difficulty)

        # 2️⃣ Convert passage to audio stream
        tts = gTTS(text=passage, lang="en")
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_stream = StreamingResponse(audio_buffer, media_type="audio/mpeg")

        # 3️⃣ Generate listening comprehension questions
        listening_questions = generate_questions(passage, num_questions=3)

        # 4️⃣ Generate pronunciation questions
        pronunciation_questions = generate_pronunciation_questions(passage, num_questions=2)

        return {
            "difficulty": difficulty,
            "listening_questions": listening_questions,
            "pronunciation_questions": pronunciation_questions,
            "audio_stream": audio_stream
        }

    except Exception as e:
      

        # Fallback safe response
        fallback_text = "Please repeat the sentence: The sun is bright today."
        tts = gTTS(text=fallback_text, lang="en")
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_stream = StreamingResponse(audio_buffer, media_type="audio/mpeg")

        return {
            "difficulty": "basic",
            "listening_questions": [{"difficulty": "basic", "question": fallback_text}],
            "pronunciation_questions": [{"difficulty": "basic", "question": fallback_text}],
            "audio_stream": audio_stream
        }