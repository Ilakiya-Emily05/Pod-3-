import os
import tempfile
from pydub import AudioSegment
from openai import OpenAI
from app.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(file_path: str) -> str:
    """
    Compress uploaded audio before sending to Whisper
    to ensure it stays under the 25MB API limit.
    """

    # Load the audio file regardless of format
    audio = AudioSegment.from_file(file_path)

    # Convert to mono 16kHz and compress to small mp3
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
        audio.export(tmp_mp3.name, format="mp3", bitrate="32k")
        compressed_path = tmp_mp3.name

    try:
        with open(compressed_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)

    return response.text
