# services/tts_service.py
import os
from gtts import gTTS
from pathlib import Path

# Directory to save generated audio
AUDIO_DIR = Path("app/static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def text_to_speech(text: str, filename: str = "generated_passage.mp3") -> str:
    """
    Convert text to speech and save as mp3.
    Returns the relative path for frontend use.
    """
    try:
        filepath = AUDIO_DIR / filename
        tts = gTTS(text=text, lang="en")
        tts.save(str(filepath))
        return f"/static/audio/{filename}"
    except Exception as e:
        
        return ""