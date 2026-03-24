# API Endpoints Documentation

## Overview

This API supports three assessment domains:

- Reading
- Listening
- Grammar

All three domains now use a CEFR-based grading model.

## CEFR Update Summary

The following changes are live across reading/listening/grammar:

1. Question-level metadata:

- `cefr_level` (A1, A2, B1, B2, C1, C2)
- `difficulty_score` (decimal)

2. Attempt result fields:

- `score` has been replaced with `ability_score`
- Attempt now includes `cefr_level` result (base levels plus optional `+`, for example `B1+`)

3. Attempt answer read model:

- `is_correct` is not returned in learner-facing response
- Response now includes CEFR snapshot fields:
  - `cefr_level`
  - `difficulty_score`

4. Assessment authoring auth:

- `POST /{domain}/assessments` requires admin auth
- `PATCH /{domain}/assessments/{assessment_id}` requires admin auth

## Authentication Rules

- Public:
  - `GET /{domain}/assessments`
  - `GET /{domain}/assessments/{assessment_id}`
- Authenticated user:
  - `POST /{domain}/attempts`
  - `POST /{domain}/attempts/{attempt_id}/submit`
- Admin only:
  - `POST /{domain}/assessments`
  - `PATCH /{domain}/assessments/{assessment_id}`

## Common Models

### CEFRLevel Enum

For question metadata:

- `A1`
- `A2`
- `B1`
- `B2`
- `C1`
- `C2`

### Attempt Result CEFR

Attempt result `cefr_level` can be:

- Base level: `A1` to `C2`
- Borderline promoted level: `A1+`, `A2+`, `B1+`, `B2+`, `C1+`

### AttemptStatus Enum

- `in_progress`
- `submitted`
- `evaluated`

### Decimal Fields

- `points`: per-question points
- `difficulty_score`: per-question difficulty input for grading
- `ability_score`: weighted CEFR ability output, range `0.0000` to `1.0000`

## Reading Endpoints

Base URL:

```text
/reading
```

### 1. Create Reading Assessment

- Endpoint: `POST /reading/assessments`
- Auth: Admin
- Status: `201 Created`

Request body:

```json
{
  "title": "Understanding Shakespeare",
  "passage_text": "William Shakespeare was an English playwright and poet...",
  "total_questions": 2,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "question_text": "What was Shakespeare's birth year?",
      "sort_order": 1,
      "points": 1.0,
      "cefr_level": "B1",
      "difficulty_score": 3.0,
      "options": [
        { "option_text": "1564", "sort_order": 1, "is_correct": true },
        { "option_text": "1600", "sort_order": 2, "is_correct": false }
      ]
    }
  ]
}
```

Response includes each question's `cefr_level` and `difficulty_score`.

### 2. List Reading Assessments

- Endpoint: `GET /reading/assessments`
- Auth: Public
- Status: `200 OK`
- Query: `is_active` (optional)

### 3. Get Reading Assessment

- Endpoint: `GET /reading/assessments/{assessment_id}`
- Auth: Public
- Status: `200 OK`, `404 Not Found`

### 4. Update Reading Assessment

- Endpoint: `PATCH /reading/assessments/{assessment_id}`
- Auth: Admin
- Status: `200 OK`, `404 Not Found`

Updatable question fields include `cefr_level` and `difficulty_score`.

### 5. Create Reading Attempt

- Endpoint: `POST /reading/attempts`
- Auth: User
- Status: `201 Created`

Request body:

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com"
}
```

Note: `user_id` and `user_email` are overridden from auth context.

Response body (shape):

```json
{
  "id": "...",
  "assessment_id": "...",
  "user_id": "...",
  "user_email": "student@example.com",
  "status": "in_progress",
  "started_at": "2026-03-24T10:15:00Z",
  "submitted_at": null,
  "total_questions": 5,
  "answered_questions": 0,
  "correct_answers": 0,
  "ability_score": null,
  "cefr_level": null,
  "answers": [],
  "created_at": "2026-03-24T10:15:00Z",
  "updated_at": "2026-03-24T10:15:00Z"
}
```

### 6. Submit Reading Attempt

- Endpoint: `POST /reading/attempts/{attempt_id}/submit`
- Auth: User
- Status: `200 OK`, `400 Bad Request`, `404 Not Found`

Request body:

```json
[
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440001",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440002"
  }
]
```

Response body (shape):

```json
{
  "id": "...",
  "status": "submitted",
  "answered_questions": 5,
  "correct_answers": 4,
  "ability_score": 0.7429,
  "cefr_level": "B1+",
  "answers": [
    {
      "id": "...",
      "question_id": "...",
      "selected_option_id": "...",
      "cefr_level": "B1",
      "difficulty_score": 3.0
    }
  ]
}
```

## Listening Endpoints

Base URL:

```text
/listening
```

### Endpoint Matrix

1. `POST /listening/assessments` (Admin)
2. `GET /listening/assessments` (Public)
3. `GET /listening/assessments/{assessment_id}` (Public)
4. `PATCH /listening/assessments/{assessment_id}` (Admin)
5. `POST /listening/attempts` (User)
6. `POST /listening/attempts/{attempt_id}/submit` (User)

Listening assessment payload differences:

- Includes `audio_url`
- Includes `audio_duration_seconds`
- Does not include `description` or `instructions`
- Questions include `cefr_level` and `difficulty_score`

Attempt responses follow the same CEFR fields as reading:

- `ability_score` instead of `score`
- result `cefr_level`
- answer snapshots: `cefr_level`, `difficulty_score`

## Grammar Endpoints

Base URL:

```text
/grammar
```

### Endpoint Matrix

1. `POST /grammar/assessments` (Admin)
2. `GET /grammar/assessments` (Public)
3. `GET /grammar/assessments/{assessment_id}` (Public)
4. `PATCH /grammar/assessments/{assessment_id}` (Admin)
5. `POST /grammar/attempts` (User)
6. `POST /grammar/attempts/{attempt_id}/submit` (User)

Grammar assessment payload differences:

- Includes optional `topic`
- Does not include `description` or `instructions`
- Questions include `cefr_level` and `difficulty_score`

Attempt responses follow the same CEFR fields as reading/listening.

## Error Handling

Common status codes:

- `200`: Success
- `201`: Resource created
- `400`: Validation or submission rule failure
- `401`: Missing/invalid auth token
- `403`: Authenticated but not allowed (admin-only endpoint)
- `404`: Assessment or attempt not found
- `500`: Internal server error

Error response format:

```json
{
  "detail": "Reading assessment not found"
}
```

## Quick Change Checklist

Use this checklist when reviewing client integrations:

1. Replace usage of `score` with `ability_score` in attempt APIs.
2. Read result `cefr_level` from attempt responses.
3. Add `cefr_level` and `difficulty_score` when creating questions.
4. Stop relying on `is_correct` in learner-facing attempt answer response.
5. Remove `description` and `instructions` from listening/grammar assessment payloads.
6. Ensure admin token is used for create/update assessment endpoints.
