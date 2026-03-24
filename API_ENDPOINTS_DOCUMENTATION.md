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
(Mock data)

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

## Mock Data for Assessment Creation
### Reading Assessment Creation

```json
{
  "title": "Giving Old Tech a Second Life",
  "passage_text": "Every year, millions of smartphones are discarded, contributing to a massive global e-waste problem. Consumers often upgrade to the latest models, leaving their previous devices to gather dust in a drawer. However, many of these older phones are still incredibly powerful and fully functional. Instead of throwing them away, tech enthusiasts are finding highly creative ways to repurpose them.\n\nOne popular project is transforming an old smartphone into a dedicated navigation device for a bicycle or motorcycle. By unlocking the device's bootloader and installing a lightweight, custom operating system, users can remove unnecessary background applications that drain the battery. The resulting device functions as an excellent, highly customizable GPS navigator. It is often more responsive than standard navigation units and doesn't risk the battery life or safety of the user's primary, expensive smartphone while out on the road.\n\nOther creative uses for outdated electronics include turning them into home security cameras, remote controls for smart home setups, or even dedicated media servers. Specialized applications can easily be downloaded to facilitate these changes. \n\nBy taking the time to give old technology a second life, individuals not only save money but also actively reduce their environmental footprint. Furthermore, tinkering with custom ROMs and hardware provides a fantastic, hands-on opportunity to learn valuable new technical skills.",
  "total_questions": 5,
  "time_limit_seconds": 600,
  "is_active": true,
  "questions": [
    {
      "question_text": "What is the primary purpose of this passage?",
      "sort_order": 1,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 4,
      "options": [
        {
          "option_text": "To convince people to stop buying the latest smartphone models.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "To explain the environmental dangers of modern e-waste.",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "To discuss how older smartphones can be successfully reused for new purposes.",
          "sort_order": 3,
          "is_correct": true
        },
        {
          "option_text": "To provide a step-by-step guide on how to install a custom operating system.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "According to the text, what is one advantage of using an old phone as a dedicated bike navigator?",
      "sort_order": 2,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 6,
      "options": [
        {
          "option_text": "It protects the battery and safety of your main, expensive smartphone.",
          "sort_order": 1,
          "is_correct": true
        },
        {
          "option_text": "It automatically connects to the internet without needing a SIM card.",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "It is entirely waterproof and cannot be damaged while riding.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "It comes with pre-installed, highly expensive navigation software.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "In the context of the first paragraph, what does the word 'discarded' mean?",
      "sort_order": 3,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 3,
      "options": [
        {
          "option_text": "Sold for a very high profit.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "Thrown away or rejected as useless.",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "Repaired using complicated tools.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "Kept safely in a secure location.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "Why might someone want to install a 'lightweight, custom operating system' on their repurposed phone?",
      "sort_order": 4,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 7,
      "options": [
        {
          "option_text": "To increase the physical weight of the phone so it doesn't fall off the bike.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "To make the phone compatible with the newest, most demanding video games.",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "To remove background apps that drain the battery, improving performance.",
          "sort_order": 3,
          "is_correct": true
        },
        {
          "option_text": "To bypass the need for a GPS signal while traveling on the road.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "Which of the following is NOT mentioned as a potential use for old electronics?",
      "sort_order": 5,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 4,
      "options": [
        {
          "option_text": "A home security camera.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "A digital picture frame.",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "A dedicated media server.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "A remote control for a smart home.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    }
  ]
}
```
### Listening Assessment Creation

```json
{
  "title": "Listening Assessment: The Fox and the Grapes",
  "audio_url": "https://ia800305.us.archive.org/30/items/aesops_fables_volume_1_librivox/fables_01_01_aesop_64kb.mp3",
  "audio_duration_seconds": 50,
  "total_questions": 5,
  "time_limit_seconds": 600,
  "is_active": true,
  "questions": [
    {
      "question_text": "What is the fox's primary goal at the beginning of the narrative?",
      "sort_order": 1,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 3,
      "options": [
        {
          "option_text": "To find a safe place to hide from a hunter.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "To reach a bunch of grapes hanging from a vine.",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "To climb a high trellis to see the surrounding area.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "To search for water to quench his thirst.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "Why is the fox ultimately unsuccessful in his attempt?",
      "sort_order": 2,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 3,
      "options": [
        {
          "option_text": "He is too exhausted from running.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "Another animal steals the food before he can get it.",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "The trellis breaks when he tries to jump on it.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "The grapes are positioned completely out of his reach.",
          "sort_order": 4,
          "is_correct": true
        }
      ]
    },
    {
      "question_text": "How does the fox behave immediately after deciding to give up?",
      "sort_order": 3,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 6,
      "options": [
        {
          "option_text": "He throws a tantrum and barks in frustration.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "He walks away adopting an attitude of dignity and unconcern.",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "He begs the other animals in the forest for help.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "He sits down and waits for the grapes to fall on their own.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "What excuse does the fox vocalize to justify his failure?",
      "sort_order": 4,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 4,
      "options": [
        {
          "option_text": "He states that he wasn't actually hungry in the first place.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "He argues that eating grapes is bad for a fox's health.",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "He claims that the grapes are likely sour anyway.",
          "sort_order": 3,
          "is_correct": true
        },
        {
          "option_text": "He says the sun was completely blinding his vision.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "Which of the following best summarizes the underlying psychological theme of this fable?",
      "sort_order": 5,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 7,
      "options": [
        {
          "option_text": "Hard work and persistence will eventually lead to success.",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "People frequently despise and belittle things they are incapable of achieving.",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "Animals are often much more intelligent than humans realize.",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "It is important to always share your food with those who are less fortunate.",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    }
  ]
}
```

### Grammar Assessment Creation

```json
{
  "title": "Grammar Assessment: Advanced Tenses",
  "topic": "Past and Perfect Tenses",
  "total_questions": 5,
  "time_limit_seconds": 300,
  "is_active": true,
  "questions": [
    {
      "question_text": "By the time the manager arrived at the office, the development team __________ the critical software update.",
      "sort_order": 1,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 5,
      "options": [
        {
          "option_text": "has finished",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "had finished",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "finished",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "was finishing",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "If the developers __________ the code more carefully, the application would not have crashed during the presentation.",
      "sort_order": 2,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 7,
      "options": [
        {
          "option_text": "checked",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "have checked",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "were checking",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "had checked",
          "sort_order": 4,
          "is_correct": true
        }
      ]
    },
    {
      "question_text": "While the server administrator __________ the network settings, the power suddenly went out.",
      "sort_order": 3,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 3,
      "options": [
        {
          "option_text": "configured",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "was configuring",
          "sort_order": 2,
          "is_correct": true
        },
        {
          "option_text": "has configured",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "had configured",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "The placement coordinator announced that the technology firm __________ three students from our batch during the previous week's interviews.",
      "sort_order": 4,
      "points": 1,
      "cefr_level": "B2",
      "difficulty_score": 6,
      "options": [
        {
          "option_text": "recruited",
          "sort_order": 1,
          "is_correct": false
        },
        {
          "option_text": "has recruited",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "had recruited",
          "sort_order": 3,
          "is_correct": true
        },
        {
          "option_text": "recruits",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    },
    {
      "question_text": "Before starting his current job, he __________ a lot of free time to experiment with different operating systems.",
      "sort_order": 5,
      "points": 1,
      "cefr_level": "B1",
      "difficulty_score": 4,
      "options": [
        {
          "option_text": "used to have",
          "sort_order": 1,
          "is_correct": true
        },
        {
          "option_text": "was having",
          "sort_order": 2,
          "is_correct": false
        },
        {
          "option_text": "has had",
          "sort_order": 3,
          "is_correct": false
        },
        {
          "option_text": "is used to having",
          "sort_order": 4,
          "is_correct": false
        }
      ]
    }
  ]
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
