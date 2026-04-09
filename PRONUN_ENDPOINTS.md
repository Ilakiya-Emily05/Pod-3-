# Endpoint Documentation

This document summarizes the current FastAPI endpoints exposed by the `phenomes_analysis` application.

## Base App
- FastAPI app configured in `app/main.py`
- Title: `AI Pronunciation & Listening Analyser`
- Version: `4.0`
- Static files mounted at `/static`
- Health check available at `/healthz`

---

## Health

### `GET /healthz`
- Tags: `Health`
- Response:
  - `{"status": "ok"}`

---

## Pronunciation Analysis

### `POST /test/analyze`
- Tags: `Pronunciation`
- Purpose: Upload spoken audio and analyze pronunciation against reference text.
- Request:
  - `file` (form-data, file) — uploaded audio file
  - `user_id` (query, UUID) — caller-provided user identifier
  - `reference_text` (query, optional string) — text to score against; if omitted, stored question from `/question/next` is used
- Behavior:
  1. Saves upload to disk
  2. Converts audio to WAV
  3. Transcribes audio using Whisper
  4. Computes pronunciation scores, phoneme details, mistakes, and tips
  5. Updates user profile / phoneme performance via post-exercise pipeline
- Success Response:
  - `request_id` (string/UUID)
  - `user_id` (UUID)
  - `reference_text` (string)
  - `transcript` (string)
  - `ref_ipa` (string)
  - `user_ipa` (string)
  - `phoneme_score` (float)
  - `fluency_score` (float)
  - `overall_score` (float)
  - `weak_phonemes` (list)
  - `strong_phonemes` (list)
  - `mistakes` (list)
  - `tips` (list)

---

## Pronunciation Question Generation

### `GET /question/next`
- Tags: `Questions`
- Purpose: Generate the next pronunciation practice prompt for a user.
- Request:
  - `user_id` (query, UUID) — user identifier
- Response:
  - `difficulty` (string)
  - `question_text` (string)
- Notes:
  - The returned question is stored in the user profile and later used by `/test/analyze` when `reference_text` is omitted.

---

## Listening Module

### `GET /listening/module`
- Tags: `Listening`
- Purpose: Generate a listening passage, audio file, and comprehension questions.
- Request:
  - `difficulty` (query, string, default `medium`) — accepted values: `easy`, `medium`, `hard`
  - `num_questions` (query, integer, default `3`) — number of comprehension questions (1 to 10)
- Response:
  - `session_id` (string)
  - `passage` (string)
  - `audio_url` (string)
  - `listening_questions` (list of question objects)
- Notes:
  - A `ListeningSession` record is created in the database to support later evaluation.

### `POST /listening/evaluate`
- Tags: `Listening`
- Purpose: Evaluate spoken answers for a generated listening session.
- Request (form-data):
  - `session_id` (string)
  - `audio_1` (file)
  - `audio_2` (file)
  - `audio_3` (file)
- Response:
  - `session_id` (string)
  - `total_score` (float)
  - `results` (list of objects):
    - `question_id` (integer)
    - `question` (string)
    - `transcript` (string)
    - `correct` (boolean)
    - `score` (float)
    - `feedback` (string)
- Notes:
  - The endpoint transcribes and evaluates all three uploaded audio answers.

---

## Pronunciation Profile

### `GET /api/v1/pronunciation/profile/{user_id}`
- Tags: `Pronunciation`
- Purpose: Retrieve a user's pronunciation profile and live phoneme statistics.
- Path Parameter:
  - `user_id` (UUID)
- Response:
  - `user_id` (UUID)
  - `current_level` (string)
  - `overall_score_avg` (float)
  - `exercises_completed` (integer)
  - `time_spent_total_mins` (float)
  - `weak_phonemes` (list of objects):
    - `phoneme` (string)
    - `error_rate` (float)
    - `example_word` (string or null)
  - `strong_phonemes` (list of objects):
    - `phoneme` (string)
    - `accuracy` (float)
  - `level_progress` (object):
    - `current` (string)
    - `exercises_at_level` (integer)
    - `required_for_next` (integer)
    - `avg_score_at_level` (float)
  - `last_practice` (timestamp or null)

---

## Pronunciation Recommendations

### `GET /api/v1/pronunciation/recommendations/{user_id}`
- Tags: `Pronunciation`
- Purpose: Return personalized practice recommendations based on the user's weak phonemes.
- Path Parameter:
  - `user_id` (UUID)
- Response:
  - `user_level` (string)
  - `focus_areas` (list of objects):
    - `phoneme` (string)
    - `accuracy_pct` (float)
    - `exercises` (list of sentence objects)
  - `suggested_practice_time_mins` (integer)
  - `next_milestone` (string)

---

## Notes
- The app mounts static assets from `settings.STATIC_AUDIO_DIR` at `/static`.
- `/test/analyze` depends on either explicit `reference_text` or a previously generated question from `/question/next`.
- The code currently contains merge-conflict artifacts in several Python files, but the active route definitions above are the documented endpoints.
