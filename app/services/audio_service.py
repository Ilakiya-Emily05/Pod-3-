# services/audio_service.py
from pydub import AudioSegment
from pathlib import Path

# Set the path to your FFmpeg binary
AudioSegment.converter = r"C:\Users\fidel\Desktop\FFmpeg\bin\ffmpeg.exe"

def convert_to_wav(file_path, audio_format: str = None) -> Path:
    """
    Convert an audio file to WAV format using pydub.

    Args:
        file_path (str or Path): Path to input audio file.
        audio_format (str, optional): Format of input file (e.g., "m4a", "mp3"). 
                                      If None, inferred from file extension.

    Returns:
        Path: Path to the converted WAV file.
    """
    # Ensure file_path is a Path object
    file_path = Path(file_path)

    # Infer format if not provided
    if audio_format is None:
        audio_format = file_path.suffix.replace(".", "").lower()

    # Load audio and export as WAV
    audio = AudioSegment.from_file(file_path, format=audio_format)
    wav_path = file_path.with_suffix(".wav")
    audio.export(wav_path, format="wav")
    return wav_path