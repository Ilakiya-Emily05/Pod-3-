import librosa
import numpy as np
import re

FILLER_WORDS = ["um", "uh", "like", "so", "you know", "actually"]

def compute_clarity(y):
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    signal_power = np.mean(y_harmonic ** 2)
    noise_power = np.mean(y_percussive ** 2) + 1e-6
    snr = signal_power / noise_power
    return min(1.0, snr / 10)

def extract_audio_features(audio_path: str, transcript: str) -> dict:
    y, sr = librosa.load(audio_path, sr=16000)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitches = pitches[magnitudes > np.median(magnitudes)]
    pitch_std = np.std(pitches) if len(pitches) > 0 else 0
    energy = np.mean(librosa.feature.rms(y=y))
    words = len(transcript.split())
    duration_sec = librosa.get_duration(y=y, sr=sr)
    wpm = (words / duration_sec) * 60 if duration_sec > 0 else 0
    rms = librosa.feature.rms(y=y)[0]
    silence_threshold = np.percentile(rms, 25)
    pauses = np.sum(rms < silence_threshold) / len(rms)
    transcript_lower = transcript.lower()
    filler_dict = {f: len(re.findall(rf"\b{f}\b", transcript_lower)) for f in FILLER_WORDS}
    volume_std = np.std(rms)
    clarity = compute_clarity(y)
    return {
        "pitch": float(pitch_std),
        "energy": float(energy),
        "speech_rate_wpm": float(wpm),
        "pauses": float(pauses),
        "filler_words": filler_dict,
        "volume_consistency": float(volume_std),
        "clarity": float(clarity)
    }

def compute_confidence(features: dict) -> int:
    score = 0
    weight_sum = 0

    pitch_score = max(0, 50 - features.get("pitch", 0) * 50)
    score += pitch_score
    weight_sum += 1

    energy_score = min(50, features.get("energy", 0) * 100)
    score += energy_score
    weight_sum += 1

    pause_score = max(0, 50 - features.get("pauses", 0) * 50)
    score += pause_score
    weight_sum += 1

    wpm = features.get("speech_rate_wpm", 0)
    wpm_score = 50 if 100 <= wpm <= 160 else max(0, 50 - abs(130 - wpm) / 2)
    score += wpm_score
    weight_sum += 1

    filler_count = sum(features.get("filler_words", {}).values())
    filler_score = max(0, 50 - filler_count * 5)
    score += filler_score
    weight_sum += 1

    volume_score = max(0, 50 - features.get("volume_consistency", 0) * 50)
    score += volume_score
    weight_sum += 1

    clarity_score = features.get("clarity", 0) * 50
    score += clarity_score
    weight_sum += 1

    confidence = score / weight_sum
    return int(round(confidence))
