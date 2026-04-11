import logging
from pathlib import Path

from app.services.llm_client import get_azure_openai_client

logger = logging.getLogger(__name__)


def transcribe_audio(file_path: str | Path) -> str:
    """
    Transcribe audio using OpenAI Whisper (whisper-1).

    Args:
        file_path: Path to the audio file

    Returns:
        Cleaned transcript string, or empty string on failure
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("transcribe_audio: file not found — path=%s", path)
        return ""

    try:
        azure_openai_client = get_azure_openai_client()
        with path.open("rb") as audio_file:
            response = azure_openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
                response_format="text",
            )

        # Defensive: ensure response is a string
        if not isinstance(response, str):
            logger.error(
                "transcribe_audio: unexpected response type — type=%s path=%s",
                type(response).__name__,
                path,
            )
            return ""

        text = response.strip().replace("\n", " ").replace("\r", " ")

        # Normalize whitespace
        text = " ".join(text.split())

        logger.info(
            "transcribe_audio: success — chars=%d preview=%s",
            len(text),
            text[:80],
        )

        return text

    except Exception as exc:
        logger.exception(
            "transcribe_audio failed — type=%s path=%s",
            type(exc).__name__,
            path,
        )
        return ""
