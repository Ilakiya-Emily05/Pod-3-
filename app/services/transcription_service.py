# app/services/transcription_service.py

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client directly here
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio using OpenAI's gpt-4o-transcribe model.
    Returns the transcript as a string.
    """
    try:
        with open(file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f
            )
        return response.text or ""
    except Exception as e:
        return ""