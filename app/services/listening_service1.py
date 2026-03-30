# services/listening_service.py
import os
import uuid
import re
import json
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
from app.prompts.question_prompt import PROMPT_LISTENING_ONLY  

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STATIC_AUDIO_DIR = "app/static/audio"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)


def generate_passage(difficulty: str) -> str:
    """
    Generate a short English passage using OpenAI for listening practice.
    """
    prompt = f"Generate a short {difficulty}-level English passage suitable for listening practice, about 3-4 sentences long."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def generate_questions_from_passage(passage: str, num_questions: int = 3):
    """
    Generate multiple unique comprehension questions in a single call to OpenAI.
    Ensures each question focuses on a different detail or idea in the passage.
    Retries once if JSON parsing fails before falling back.
    """
   

    # Inject the passage into the prompt
    prompt_text = PROMPT_LISTENING_ONLY.replace("{passage}", passage).replace("{num_listening}", str(num_questions))

    for attempt in range(2):  # try twice before fallback
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
                max_tokens=400
            )
            raw_text = response.choices[0].message.content.strip()

            # Extract JSON array safely
            match = re.search(r"(\[.*\])", raw_text, flags=re.DOTALL)
            if match:
                questions = json.loads(match.group(1))
                # Add id fields if missing
                for idx, q in enumerate(questions):
                    if "id" not in q:
                        q["id"] = idx + 1
                return questions

        except Exception as e:
            
            continue

    # fallback if all attempts fail
    return [{"id": i + 1, "text": f"Question {i + 1}"} for i in range(num_questions)]



         


def generate_listening_module(difficulty: str = "medium", num_questions: int = 3):
    """
    Generates a listening passage, TTS audio file, and comprehension questions.
    Returns a JSON with 'passage', 'audio_url', and 'listening_questions'.
    """
    try:
        # 1. Generate passage
        passage = generate_passage(difficulty)

        # 2. Generate unique questions from passage
        listening_questions = generate_questions_from_passage(passage, num_questions)

        # 3. Generate TTS audio and save to file
        audio_filename = f"listening_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(STATIC_AUDIO_DIR, audio_filename)
        tts = gTTS(text=passage, lang="en")
        tts.save(audio_path)

        # 4. Return URL for frontend
        audio_url = f"/static/audio/{audio_filename}"

        return {
            "passage": passage,
            "audio_url": audio_url,
            "listening_questions": listening_questions
        }

    except Exception as e:
       
        # Fallback if OpenAI fails
        fallback_text = "Please repeat the sentence: The sun is bright today."
        fallback_filename = "fallback_passage.mp3"
        tts = gTTS(text=fallback_text, lang="en")
        tts.save(os.path.join(STATIC_AUDIO_DIR, fallback_filename))
        return {
            "passage": fallback_text,
            "audio_url": f"/static/audio/{fallback_filename}",
            "listening_questions": [{"id": 1, "text": fallback_text}]
        }