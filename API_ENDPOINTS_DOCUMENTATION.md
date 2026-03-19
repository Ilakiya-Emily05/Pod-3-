# API Endpoints Documentation

## Assessment Types

This document outlines the API endpoints structure for three assessment types:

- **Reading Assessment**: Assessments with reading passages and comprehension questions
- **Listening Assessment**: Assessments with audio content and listening comprehension questions
- **Grammar Assessment**: Grammar-focused assessments with multiple-choice questions

---

## Table of Contents

1. [Reading Assessment Endpoints](#reading-assessment-endpoints)
2. [Listening Assessment Endpoints](#listening-assessment-endpoints)
3. [Grammar Assessment Endpoints](#grammar-assessment-endpoints)
4. [Common Response Models](#common-response-models)
5. [Error Handling](#error-handling)
6. [Authentication](#authentication)

---

## Reading Assessment Endpoints

### Overview

Reading assessments contain a passage text and multiple questions based on that passage. Users can take attempts on these assessments.

### Base URL

```
/reading
```

### 1. Create Reading Assessment

**Endpoint:** `POST /reading/assessments`  
**Status Code:** 201 Created  
**Authentication:** Not Required  
**Description:** Creates a new reading assessment with questions and options.

**Request Body:**

```json
{
  "title": "Understanding Shakespeare",
  "passage_text": "William Shakespeare was an English playwright and poet who lived from 1564 to 1616...",
  "total_questions": 5,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "question_text": "What was Shakespeare's birth year?",
      "sort_order": 1,
      "points": 2.5,
      "options": [
        {
          "option_text": "1564",
          "sort_order": 1,
          "is_correct": true
        },
        {
          "option_text": "1600",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "1550",
          "sort_order": 3,
          "is_correct": false
        }
      ]
    }
  ]
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Understanding Shakespeare",
  "passage_text": "William Shakespeare was an English playwright and poet...",
  "total_questions": 5,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
      "question_text": "What was Shakespeare's birth year?",
      "sort_order": 1,
      "points": 2.5,
      "options": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "option_text": "1564",
          "sort_order": 1,
          "is_correct": true,
          "created_at": "2024-03-19T10:00:00Z",
          "updated_at": "2024-03-19T10:00:00Z"
        }
      ],
      "created_at": "2024-03-19T10:00:00Z",
      "updated_at": "2024-03-19T10:00:00Z"
    }
  ],
  "created_at": "2024-03-19T10:00:00Z",
  "updated_at": "2024-03-19T10:00:00Z"
}
```

**Field Descriptions:**

- `title` (string, required): Assessment title (1-255 characters)
- `passage_text` (string, required): The reading passage content
- `total_questions` (integer): Total number of questions (≥ 0)
- `time_limit_seconds` (integer, optional): Time limit in seconds (≥ 1)
- `is_active` (boolean): Whether the assessment is active (default: true)
- `questions` (array): List of questions with options
  - `question_text` (string): The question content
  - `sort_order` (integer): Display order (≥ 1)
  - `points` (decimal): Points for this question (≥ 0)
  - `options` (array): Multiple choice options
    - `option_text` (string): The option text
    - `sort_order` (integer): Display order
    - `is_correct` (boolean): Whether this is the correct answer

---

### 2. List Reading Assessments

**Endpoint:** `GET /reading/assessments`  
**Status Code:** 200 OK  
**Authentication:** Not Required  
**Description:** Retrieves all reading assessments with optional filtering.

**Query Parameters:**

- `is_active` (boolean, optional): Filter by active status (true/false)

**Example Request:**

```
GET /reading/assessments?is_active=true
```

**Response Body:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Understanding Shakespeare",
    "passage_text": "William Shakespeare was an English playwright...",
    "total_questions": 5,
    "time_limit_seconds": 300,
    "is_active": true,
    "questions": [],
    "created_at": "2024-03-19T10:00:00Z",
    "updated_at": "2024-03-19T10:00:00Z"
  }
]
```

---

### 3. Get Reading Assessment by ID

**Endpoint:** `GET /reading/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Description:** Retrieves a specific reading assessment with all its questions and options.

**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

**Example Request:**

```
GET /reading/assessments/550e8400-e29b-41d4-a716-446655440000
```

**Response Body:** (Same as Create response)

---

### 4. Update Reading Assessment

**Endpoint:** `PATCH /reading/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Description:** Partially updates a reading assessment.

**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

**Request Body (all fields optional):**

```json
{
  "title": "Updated Shakespeare Assessment",
  "passage_text": "Updated passage text...",
  "total_questions": 6,
  "time_limit_seconds": 400,
  "is_active": false
}
```

**Response Body:** (Same as Create response)

---

### 5. Create Reading Attempt

**Endpoint:** `POST /reading/attempts`  
**Status Code:** 201 Created  
**Authentication:** Required (Bearer Token)  
**Description:** Creates a new attempt for a reading assessment by a user.

**Request Body:**

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com"
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "in_progress",
  "started_at": "2024-03-19T10:15:00Z",
  "submitted_at": null,
  "total_questions": 5,
  "answered_questions": 0,
  "correct_answers": 0,
  "score": 0.0,
  "answers": [],
  "created_at": "2024-03-19T10:15:00Z",
  "updated_at": "2024-03-19T10:15:00Z"
}
```

**Field Descriptions:**

- `assessment_id` (UUID, required): ID of the assessment to attempt
- `user_id` (UUID, optional): ID of the user attempting
- `user_email` (string, optional): Email of the user (≤ 320 characters)
- `status` (string): Current status (in_progress, submitted, etc.)
- `started_at` (datetime): When the attempt started
- `submitted_at` (datetime, optional): When the attempt was submitted
- `total_questions` (integer): Total questions in assessment
- `answered_questions` (integer): Number of questions answered
- `correct_answers` (integer): Number of correct answers
- `score` (decimal): Total score achieved

---

### 6. Submit Reading Attempt

**Endpoint:** `POST /reading/attempts/{attempt_id}/submit`  
**Status Code:** 200 OK | 400 Bad Request | 404 Not Found  
**Authentication:** Required (Bearer Token)  
**Description:** Submits answers for a reading attempt and calculates the score.

**Path Parameters:**

- `attempt_id` (UUID, required): The attempt ID

**Request Body:**

```json
[
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440001",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440002"
  },
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440005",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440006"
  }
]
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "submitted",
  "started_at": "2024-03-19T10:15:00Z",
  "submitted_at": "2024-03-19T10:25:00Z",
  "total_questions": 5,
  "answered_questions": 5,
  "correct_answers": 4,
  "score": 10.0,
  "answers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "question_id": "550e8400-e29b-41d4-a716-446655440001",
      "selected_option_id": "550e8400-e29b-41d4-a716-446655440002",
      "is_correct": true
    }
  ],
  "created_at": "2024-03-19T10:15:00Z",
  "updated_at": "2024-03-19T10:25:00Z"
}
```

**Answer Field Descriptions:**

- `question_id` (UUID, required): ID of the question
- `selected_option_id` (UUID, optional): ID of the selected option (null if not answered)
- `is_correct` (boolean): Whether the answer is correct (populated on submission)

---

## Listening Assessment Endpoints

### Overview

Listening assessments contain audio content and multiple questions based on that audio. Similar structure to reading assessments but with audio-specific fields.

### Base URL

```
/listening
```

### 1. Create Listening Assessment

**Endpoint:** `POST /listening/assessments`  
**Status Code:** 201 Created  
**Authentication:** Not Required  
**Description:** Creates a new listening assessment with audio and questions.

**Request Body:**

```json
{
  "title": "English Conversation 101",
  "description": "Listening comprehension based on a daily conversation",
  "instructions": "Listen to the audio carefully and answer the following questions",
  "audio_url": "https://example.com/audios/conversation-101.mp3",
  "audio_duration_seconds": 180,
  "total_questions": 4,
  "time_limit_seconds": 600,
  "is_active": true,
  "questions": [
    {
      "question_text": "Where is the conversation taking place?",
      "sort_order": 1,
      "points": 2.0,
      "options": [
        {
          "option_text": "At a coffee shop",
          "sort_order": 1,
          "is_correct": true
        },
        {
          "option_text": "At a restaurant",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "At a library",
          "sort_order": 3,
          "is_correct": false
        }
      ]
    }
  ]
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "title": "English Conversation 101",
  "description": "Listening comprehension based on a daily conversation",
  "instructions": "Listen to the audio carefully and answer the following questions",
  "audio_url": "https://example.com/audios/conversation-101.mp3",
  "audio_duration_seconds": 180,
  "total_questions": 4,
  "time_limit_seconds": 600,
  "is_active": true,
  "questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440011",
      "assessment_id": "550e8400-e29b-41d4-a716-446655440010",
      "question_text": "Where is the conversation taking place?",
      "sort_order": 1,
      "points": 2.0,
      "options": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440012",
          "option_text": "At a coffee shop",
          "sort_order": 1,
          "is_correct": true,
          "created_at": "2024-03-19T10:00:00Z",
          "updated_at": "2024-03-19T10:00:00Z"
        }
      ],
      "created_at": "2024-03-19T10:00:00Z",
      "updated_at": "2024-03-19T10:00:00Z"
    }
  ],
  "created_at": "2024-03-19T10:00:00Z",
  "updated_at": "2024-03-19T10:00:00Z"
}
```

**Field Descriptions:**

- `title` (string, required): Assessment title (1-255 characters)
- `description` (string, optional): Description of the assessment
- `instructions` (string, optional): Instructions for the student
- `audio_url` (string, required): URL to the audio file (1-1024 characters)
- `audio_duration_seconds` (integer, optional): Duration of audio in seconds (≥ 1)
- `total_questions` (integer): Total number of questions (≥ 0)
- `time_limit_seconds` (integer, optional): Time limit in seconds (≥ 1)
- `is_active` (boolean): Whether the assessment is active (default: true)
- `questions` (array): List of questions with options (same structure as Reading)

---

### 2. List Listening Assessments

**Endpoint:** `GET /listening/assessments`  
**Status Code:** 200 OK  
**Authentication:** Not Required  
**Query Parameters:**

- `is_active` (boolean, optional): Filter by active status

**Example Request:**

```
GET /listening/assessments?is_active=true
```

---

### 3. Get Listening Assessment by ID

**Endpoint:** `GET /listening/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

---

### 4. Update Listening Assessment

**Endpoint:** `PATCH /listening/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

**Request Body (all fields optional):**

```json
{
  "title": "Updated English Conversation",
  "audio_url": "https://example.com/audios/new-conversation.mp3",
  "audio_duration_seconds": 240,
  "is_active": true
}
```

---

### 5. Create Listening Attempt

**Endpoint:** `POST /listening/attempts`  
**Status Code:** 201 Created  
**Authentication:** Required (Bearer Token)  
**Description:** Creates a new attempt for a listening assessment.

**Request Body:**

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440010",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com"
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440013",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440010",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "in_progress",
  "started_at": "2024-03-19T10:30:00Z",
  "submitted_at": null,
  "total_questions": 4,
  "answered_questions": 0,
  "correct_answers": 0,
  "score": 0.0,
  "answers": [],
  "created_at": "2024-03-19T10:30:00Z",
  "updated_at": "2024-03-19T10:30:00Z"
}
```

---

### 6. Submit Listening Attempt

**Endpoint:** `POST /listening/attempts/{attempt_id}/submit`  
**Status Code:** 200 OK | 400 Bad Request | 404 Not Found  
**Authentication:** Required (Bearer Token)  
**Path Parameters:**

- `attempt_id` (UUID, required): The attempt ID

**Request Body:**

```json
[
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440011",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440012"
  },
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440014",
    "selected_option_id": null
  }
]
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440013",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440010",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "submitted",
  "started_at": "2024-03-19T10:30:00Z",
  "submitted_at": "2024-03-19T10:45:00Z",
  "total_questions": 4,
  "answered_questions": 3,
  "correct_answers": 3,
  "score": 6.0,
  "answers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440015",
      "question_id": "550e8400-e29b-41d4-a716-446655440011",
      "selected_option_id": "550e8400-e29b-41d4-a716-446655440012",
      "is_correct": true
    }
  ],
  "created_at": "2024-03-19T10:30:00Z",
  "updated_at": "2024-03-19T10:45:00Z"
}
```

---

## Grammar Assessment Endpoints

### Overview

Grammar assessments focus on grammar topics with targeted multiple-choice questions. Similar structure to reading and listening assessments but with grammar-specific fields.

### Base URL

```
/grammar
```

### 1. Create Grammar Assessment

**Endpoint:** `POST /grammar/assessments`  
**Status Code:** 201 Created  
**Authentication:** Not Required  
**Description:** Creates a new grammar assessment with questions.

**Request Body:**

```json
{
  "title": "Present Perfect Tense",
  "description": "Test your understanding of present perfect tense usage",
  "instructions": "Choose the correct option for each sentence",
  "topic": "Verb Tenses",
  "total_questions": 6,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "question_text": "She ____ to Paris three times.",
      "sort_order": 1,
      "points": 1.5,
      "options": [
        {
          "option_text": "has gone",
          "sort_order": 1,
          "is_correct": true
        },
        {
          "option_text": "goes",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "went",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "is going",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    }
  ]
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440020",
  "title": "Present Perfect Tense",
  "description": "Test your understanding of present perfect tense usage",
  "instructions": "Choose the correct option for each sentence",
  "topic": "Verb Tenses",
  "total_questions": 6,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440021",
      "assessment_id": "550e8400-e29b-41d4-a716-446655440020",
      "question_text": "She ____ to Paris three times.",
      "sort_order": 1,
      "points": 1.5,
      "options": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440022",
          "option_text": "has gone",
          "sort_order": 1,
          "is_correct": true,
          "created_at": "2024-03-19T10:00:00Z",
          "updated_at": "2024-03-19T10:00:00Z"
        }
      ],
      "created_at": "2024-03-19T10:00:00Z",
      "updated_at": "2024-03-19T10:00:00Z"
    }
  ],
  "created_at": "2024-03-19T10:00:00Z",
  "updated_at": "2024-03-19T10:00:00Z"
}
```

**Field Descriptions:**

- `title` (string, required): Assessment title (1-255 characters)
- `description` (string, optional): Description of the assessment
- `instructions` (string, optional): Instructions for the student
- `topic` (string, optional): Grammar topic (≤ 255 characters)
- `total_questions` (integer): Total number of questions (≥ 0)
- `time_limit_seconds` (integer, optional): Time limit in seconds (≥ 1)
- `is_active` (boolean): Whether the assessment is active (default: true)
- `questions` (array): List of questions with options (same structure as Reading/Listening)

---

### 2. List Grammar Assessments

**Endpoint:** `GET /grammar/assessments`  
**Status Code:** 200 OK  
**Authentication:** Not Required  
**Query Parameters:**

- `is_active` (boolean, optional): Filter by active status

**Example Request:**

```
GET /grammar/assessments?is_active=true
```

---

### 3. Get Grammar Assessment by ID

**Endpoint:** `GET /grammar/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

---

### 4. Update Grammar Assessment

**Endpoint:** `PATCH /grammar/assessments/{assessment_id}`  
**Status Code:** 200 OK | 404 Not Found  
**Authentication:** Not Required  
**Path Parameters:**

- `assessment_id` (UUID, required): The assessment ID

**Request Body (all fields optional):**

```json
{
  "title": "Advanced Present Perfect Tense",
  "topic": "Advanced Verb Tenses",
  "total_questions": 8,
  "is_active": true
}
```

---

### 5. Create Grammar Attempt

**Endpoint:** `POST /grammar/attempts`  
**Status Code:** 201 Created  
**Authentication:** Required (Bearer Token)  
**Description:** Creates a new attempt for a grammar assessment.

**Request Body:**

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440020",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com"
}
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440023",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440020",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "in_progress",
  "started_at": "2024-03-19T11:00:00Z",
  "submitted_at": null,
  "total_questions": 6,
  "answered_questions": 0,
  "correct_answers": 0,
  "score": 0.0,
  "answers": [],
  "created_at": "2024-03-19T11:00:00Z",
  "updated_at": "2024-03-19T11:00:00Z"
}
```

---

### 6. Submit Grammar Attempt

**Endpoint:** `POST /grammar/attempts/{attempt_id}/submit`  
**Status Code:** 200 OK | 400 Bad Request | 404 Not Found  
**Authentication:** Required (Bearer Token)  
**Path Parameters:**

- `attempt_id` (UUID, required): The attempt ID

**Request Body:**

```json
[
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440021",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440022"
  },
  {
    "question_id": "550e8400-e29b-41d4-a716-446655440024",
    "selected_option_id": "550e8400-e29b-41d4-a716-446655440025"
  }
]
```

**Response Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440023",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440020",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "user_email": "student@example.com",
  "status": "submitted",
  "started_at": "2024-03-19T11:00:00Z",
  "submitted_at": "2024-03-19T11:10:00Z",
  "total_questions": 6,
  "answered_questions": 6,
  "correct_answers": 5,
  "score": 7.5,
  "answers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440026",
      "question_id": "550e8400-e29b-41d4-a716-446655440021",
      "selected_option_id": "550e8400-e29b-41d4-a716-446655440022",
      "is_correct": true
    }
  ],
  "created_at": "2024-03-19T11:00:00Z",
  "updated_at": "2024-03-19T11:10:00Z"
}
```

---

## Common Response Models

### AttemptStatus Enum

Possible values for attempt status:

- `in_progress`: Attempt has been started but not submitted
- `submitted`: Attempt has been submitted and graded

### UUID Format

All IDs in responses use UUID v4 format, example:

```
550e8400-e29b-41d4-a716-446655440000
```

### Datetime Format

All timestamps use ISO 8601 format with UTC timezone:

```
2024-03-19T10:00:00Z
```

### Decimal/Number Fields

- `points`: Assessment item points (e.g., 2.5, 1.0)
- `score`: Total score achieved (e.g., 10.0, 7.5)
- Can contain up to 2 decimal places for scores

---

## Error Handling

### Common HTTP Status Codes

| Status Code | Description                                              |
| ----------- | -------------------------------------------------------- |
| 200         | OK - Request successful                                  |
| 201         | Created - Resource created successfully                  |
| 400         | Bad Request - Invalid input or attempt already submitted |
| 404         | Not Found - Assessment or attempt not found              |
| 500         | Internal Server Error - Server-side error                |

### Error Response Format

```json
{
  "detail": "Reading assessment not found"
}
```

### Common Error Scenarios

**Assessment Not Found (404):**

```
GET /reading/assessments/550e8400-e29b-41d4-a716-446655440099

Response:
{
  "detail": "Reading assessment not found"
}
```

**Invalid Attempt Submission (400):**

```
POST /reading/attempts/{attempt_id}/submit with invalid answer data

Response:
{
  "detail": "Invalid answer format or attempt already submitted"
}
```

---

## Authentication

### Bearer Token Authentication

Endpoints that require authentication need a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Authenticated Endpoints

- `POST /reading/attempts` - Create attempt
- `POST /reading/attempts/{attempt_id}/submit` - Submit attempt
- `POST /listening/attempts` - Create attempt
- `POST /listening/attempts/{attempt_id}/submit` - Submit attempt
- `POST /grammar/attempts` - Create attempt
- `POST /grammar/attempts/{attempt_id}/submit` - Submit attempt

### Current User ID

Authenticated endpoints extract the current user ID from the JWT token and use it for authorization.

---

## Summary Table

| Operation         | Reading                            | Listening                            | Grammar                            |
| ----------------- | ---------------------------------- | ------------------------------------ | ---------------------------------- |
| Create Assessment | POST /reading/assessments          | POST /listening/assessments          | POST /grammar/assessments          |
| List Assessments  | GET /reading/assessments           | GET /listening/assessments           | GET /grammar/assessments           |
| Get Assessment    | GET /reading/assessments/{id}      | GET /listening/assessments/{id}      | GET /grammar/assessments/{id}      |
| Update Assessment | PATCH /reading/assessments/{id}    | PATCH /listening/assessments/{id}    | PATCH /grammar/assessments/{id}    |
| Create Attempt    | POST /reading/attempts             | POST /listening/attempts             | POST /grammar/attempts             |
| Submit Attempt    | POST /reading/attempts/{id}/submit | POST /listening/attempts/{id}/submit | POST /grammar/attempts/{id}/submit |

---

## TODO
- Add a role based access control section for admin vs student permissions
- Authenticate API endpoints like (create, update, delete) for assessments to admin users only
- Add pagination support for listing assessments and attempts