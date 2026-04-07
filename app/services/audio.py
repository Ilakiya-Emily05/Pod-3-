import logging
import os
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Allow optional override via environment variable (e.g., for Docker images)
_ffmpeg_path = os.getenv("FFMPEG_PATH")
if _ffmpeg_path:
    AudioSegment.converter = _ffmpeg_path


def convert_to_wav(file_path: str | Path, audio_format: str | None = None) -> Path:
    """
    Convert an audio file to WAV format.

    Args:
        file_path: Path to the source audio file.
        audio_format: Optional explicit format (e.g. "m4a").
                      If None, inferred from the file extension.

    Returns:
        Path to the converted .wav file (same directory as source).

    Raises:
        FileNotFoundError: If the source file does not exist.
        RuntimeError: If pydub/ffmpeg conversion fails.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    fmt = audio_format or file_path.suffix.lstrip(".").lower()
    if not fmt:
        raise ValueError(f"Cannot infer audio format from: {file_path}")

    wav_path = file_path.with_suffix(".wav")

    # Skip conversion if already WAV
    if fmt == "wav" and file_path == wav_path:
        return wav_path

    try:
        audio = AudioSegment.from_file(file_path, format=fmt)
        audio.export(wav_path, format="wav")
        logger.debug("Audio converted: %s → %s", file_path, wav_path)
        return wav_path
    except Exception as exc:
        raise RuntimeError(f"Audio conversion failed for {file_path}: {exc}") from exc
