---
description: Audio-first interview flow — Practice and Mock Interview
---

# Audio-First Interview Flow

This documents the end-to-end flow for both AI Practice (Section 1) and Mock Interview (Section 2). All user input is audio. Text answers are no longer accepted.

---

## Prerequisites

1. Resume has been parsed and keywords ingested via:
   ```
   POST /resume/parse
   POST /api/v1/keywords/ingest   (called internally after parse)
   ```
   This generates open-ended questions (Easy/Medium/Hard) per skill keyword in the DB.

---

## Section 1 — AI Practice

### Step 1: Fetch a Question
```
GET /api/v1/practice/questions/start?user_id={user_id}
```
- Returns a question with no options (open-ended).
- Automatically picks unanswered questions; if all answered, returns 404.

### Step 2: Submit Audio Answer
```
POST /api/v1/practice/answer
Content-Type: multipart/form-data

Fields:
  user_id   (string, required)
  question_id (UUID, required)
  file      (audio file, required — mp3/wav/m4a/webm)
```
**Backend pipeline:**
1. Save audio to temp file.
2. `transcribe_audio(path)` → Whisper `whisper-1` → plain text transcript.
3. `extract_audio_features(path, transcript)` → pitch, WPM, pauses, fillers, clarity.
4. `compute_confidence(features)` → integer score (0–50).
5. `evaluate_answer(question, ideal_answer, transcript)` → LLM semantic match → `(is_correct, feedback)`.
6. Save `UserResponse` (session_id=NULL for practice).
7. Fetch next question (excluding all previously answered).

**Response:**
```json
{
  "is_correct": true,
  "feedback": "Good explanation of ...",
  "confidence_score": 38,
  "transcription": "I think the answer is ...",
  "next_question": { "id": "...", "text": "...", "difficulty": "medium" },
  "practice_complete": false
}
```

### Step 3: Repeat Step 2 until `practice_complete: true`

---

## Section 2 — Mock Interview

### Step 1: Start Session
```
POST /api/v1/interviews/sessions
Content-Type: application/json

{ "user_id": "abc123" }
```
**Backend logic:**
1. Compute `globally_excluded` = practice-answered IDs ∪ prior mock session IDs.
2. Count available questions not in `globally_excluded`.
3. If available < 3 → auto-generate fresh questions via LLM for each skill.
4. Create `InterviewSession`, pick first question (Easy).

**Response:**
```json
{
  "session_id": "uuid",
  "status": "active",
  "current_question": { "id": "...", "text": "..." }
}
```

### Step 2: Submit Audio Answer
```
POST /api/v1/interviews/sessions/{session_id}/answer
Content-Type: multipart/form-data

Fields:
  file  (audio file, required)
```
**Backend pipeline:** Same as Practice (Whisper → features → confidence → LLM eval).
- Evaluation is **hidden** from user during session (no feedback shown).
- Exclusion: `globally_excluded ∪ current_session_answered` — zero repeats.

**Response:**
```json
{
  "session_complete": false,
  "next_question": { "id": "...", "text": "..." },
  "transcription": "...",
  "confidence_score": 42
}
```

### Step 3: Repeat Step 2 until `session_complete: true`

> Session ends when 5 minutes have elapsed (timer starts at session creation).

### Step 4: Fetch Gap Analysis
```
GET /api/v1/interviews/sessions/{session_id}/feedback
```
**Response:**
```json
{
  "session_id": "uuid",
  "feedback": "STRENGTHS: ... WEAKNESSES: ... RECOMMENDATIONS: ..."
}
```

---

## New Frontend Endpoints

### List All Sessions for a Candidate
```
GET /api/v1/mock/sessions?candidate_id={user_id}
```
**Response:**
```json
[
  {
    "session_id": "uuid",
    "status": "completed",
    "created_at": "2026-03-26T12:00:00Z",
    "response_count": 7
  }
]
```

### Detailed Result for One Session
```
GET /api/v1/mock/session/{session_id}/result
```
**Response:**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "gap_analysis": "STRENGTHS: ...",
  "responses": [
    {
      "question_text": "Explain polymorphism.",
      "user_answer": "Polymorphism means...",
      "confidence_score": 40,
      "is_correct": true,
      "feedback": "Good answer."
    }
  ]
}
```

---

## Error Cases

| Scenario | HTTP | Message |
|----------|------|---------|
| No audio file uploaded | 422 | Validation error |
| Session not found | 400 | `Session not found or already completed` |
| Session still active (result fetch) | 400 | `Session is still active` |
| No skills/questions in DB | 400 | `No skills found for user` |
| Whisper fails | 500 | Unhandled error |
