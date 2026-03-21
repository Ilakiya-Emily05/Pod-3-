import os
import tempfile
from pydub import AudioSegment
from openai import OpenAI
from app.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def transcribe_audio(file_path: str) -> str:
    suffix = os.path.splitext(file_path)[1].lower()
    if suffix != ".wav":
        audio = AudioSegment.from_file(file_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            audio.export(tmp_wav.name, format="wav")
            wav_path = tmp_wav.name
    else:
        wav_path = file_path

    try:
        with open(wav_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
    finally:
        if suffix != ".wav" and os.path.exists(wav_path):
            os.remove(wav_path)

    return response.text
