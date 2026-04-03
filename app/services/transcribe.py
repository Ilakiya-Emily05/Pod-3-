import os
import tempfile
from pydub import AudioSegment
from openai import AsyncOpenAI  # ← change to AsyncOpenAI
from app.config.settings import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)  # ← AsyncOpenAI


async def transcribe_audio(file_path: str) -> str:
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
        audio.export(tmp_mp3.name, format="mp3", bitrate="32k")
        compressed_path = tmp_mp3.name

    try:
        with open(compressed_path, "rb") as f:
            response = await client.audio.transcriptions.create(  # ← add await
                model="whisper-1",
                file=f
            )
    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)

    return response.text