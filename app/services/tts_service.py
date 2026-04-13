import logging
from pathlib import Path

from gtts import gTTS

from app.config.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

AUDIO_DIR = Path(settings.static_audio_dir)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def text_to_speech(text: str, filename: str) -> str:
    try:
        filepath = AUDIO_DIR / filename
        tts = gTTS(text=text, lang="en")
        tts.save(str(filepath))
        logger.info("TTS saved: %s", filepath)
        return f"/static/audio/{filename}"
    except Exception as exc:
        logger.error(
            "TTS failed — type=%s reason=%s filename=%s", type(exc).__name__, exc, filename
        )
        return ""
