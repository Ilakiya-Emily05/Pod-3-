# Database Schema Documentation

## Table of Contents

1. [Entity Relationship Diagram](#entity-relationship-diagram)
2. [Database Tables Overview](#database-tables-overview)
3. [Detailed Table Mappings](#detailed-table-mappings)
4. [Relationships & Foreign Keys](#relationships--foreign-keys)
5. [Normalization Principles](#normalization-principles)
6. [Data Examples](#data-examples)

---

## Entity Relationship Diagram

![ER Diagram](https://mermaid.ink/svg/pako:eNqVVNtqg0AQ_ZUwz0lQY73smzQ2BBqTupZCEWSJkwupa9kYaGvz77VpYi_uot0nlzmXmTO4JSzzFIEAivGWrQXLYt6rzj31Q9p7fx8M8vJ0SRbh_GZ661PS27C9BDQJvdnMCxMvivzZIqpwBduhDBn63ngaTDogb6c08gMp9gtdm1LqUzrzg6jRz929T6PpPKioy5wXbMv3v7k1QMVM5ouzQD15B9_vjpusc0lBSbyAPlQp_LvhBl_gCgXyJSoULpO1Cu3xCZcFpsmWX6Kvt9iM4FJSRt8AqJiS6Dv4SqL_W1JQVNG3NtwavWqyViFJ9D9-i2YI30Vl_BKImi1ZQUd_yRqaRSVNtYpOzbeuQz1nB7EfK4E-rMU2BbJiT3vsQ4YiY593KD-NYig2mGEMpPpMmdjFEPNjRXpm_DHPMyCFOFQ0kR_Wm1rk8JyyAs_vcQ1BnqK4zg-8AGJazkkDSAkvQFxraJqmZruO7RhXmmb04RWIMXKGzki_0jXNNF3btZ1jH95OrtrQtS3XcC3LtHTd0S3z-AGLT9aD)

---

## Database Tables Overview

The database is structured in **4 main domains** based on assessment types:

1. **User Management Domain** - User authentication and profile data
2. **Grammar Assessment Domain** - Grammar exercises and user attempts
3. **Reading Assessment Domain** - Reading comprehension exercises and user attempts
4. **Listening Assessment Domain** - Listening comprehension exercises and user attempts

Each assessment domain follows the same hierarchical pattern:

- **Assessment** (template/blueprint)
- **Questions** (belongs to assessment)
- **Question Options** (belongs to question)
- **Attempts** (user attempts at assessment)
- **Attempt Answers** (user's individual answers)

---

## Detailed Table Mappings

### 1. USERS Table

**Purpose**: Core authentication and account management table. Stores user credentials and authentication provider information for OAuth integration.

| Column              | Type         | Constraints               | Explanation                                                                 |
| ------------------- | ------------ | ------------------------- | --------------------------------------------------------------------------- |
| `id`                | UUID         | Primary Key               | Unique identifier for each user, auto-generated UUID v4                     |
| `email`             | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | User's email address, used for login and authentication                     |
| `password_hash`     | VARCHAR(255) | NULLABLE                  | Bcrypt/Argon2 hash of password. NULL if using OAuth                         |
| `oauth_provider`    | VARCHAR(50)  | NULLABLE                  | OAuth provider name (e.g., 'google', 'github'). NULL if using password auth |
| `oauth_sub`         | VARCHAR(255) | NULLABLE                  | OAuth subject/ID from provider. Multiple users can share same oauth_sub     |
| `is_active`         | BOOLEAN      | NOT NULL, DEFAULT=TRUE    | Soft delete flag; false indicates deactivated account                       |
| `profile_completed` | BOOLEAN      | NOT NULL, DEFAULT=FALSE   | Whether user has completed onboarding profile                               |
| `created_at`        | TIMESTAMP    | NOT NULL, DEFAULT=NOW()   | Account creation timestamp                                                  |

**Why this table exists**:

- Foundation for user authentication and session management
- Supports both traditional login (password) and OAuth authentication
- Tracks account activation status without hard deletes

**Sample Row**:

```
id: 550e8400-e29b-41d4-a716-446655440001
email: john.doe@example.com
password_hash: $2b$12$KIXxPfL7v8Z1q.R8mNoqduL4w.hzWj8GZqDtTlKj3k8...
oauth_provider: NULL
oauth_sub: NULL
is_active: true
profile_completed: true
created_at: 2024-01-15 10:30:00+00
```

---

### 2. USER_PROFILES Table

**Purpose**: Extended user information beyond authentication. Stores personal and demographic details collected during onboarding.

| Column       | Type         | Constraints                                       | Explanation                                           |
| ------------ | ------------ | ------------------------------------------------- | ----------------------------------------------------- |
| `id`         | UUID         | Primary Key                                       | Unique identifier for profile record                  |
| `user_id`    | UUID         | Foreign Key (users.id), UNIQUE, NOT NULL, CASCADE | Links to parent user; UNIQUE ensures 1:1 relationship |
| `name`       | VARCHAR(255) | NOT NULL                                          | User's full name                                      |
| `mobile`     | VARCHAR(20)  | NOT NULL                                          | Phone number for contact                              |
| `dob`        | VARCHAR(10)  | NOT NULL                                          | Date of birth (format: YYYY-MM-DD)                    |
| `college`    | VARCHAR(255) | NOT NULL                                          | Educational institution name                          |
| `created_at` | TIMESTAMP    | NOT NULL, DEFAULT=NOW()                           | Profile creation timestamp                            |
| `updated_at` | TIMESTAMP    | NOT NULL, DEFAULT=NOW(), ONUPDATE=NOW()           | Profile last modification timestamp                   |

**Why this table exists**:

- Separates authentication data (USERS) from personal data (USER_PROFILES)
- Allows optional profile completion (user can have account without profile)
- Follows Single Responsibility Principle in database design

**Relationship**: One user has at most one profile (1:0..1)

**Sample Row**:

```
id: 660e8400-e29b-41d4-a716-446655440002
user_id: 550e8400-e29b-41d4-a716-446655440001
name: John Doe
mobile: +1-800-123-4567
dob: 1998-05-20
college: MIT
created_at: 2024-01-15 10:35:00+00
updated_at: 2024-01-15 10:35:00+00
```

---

### 3. GRAMMAR_ASSESSMENTS Table

**Purpose**: Template/blueprint for grammar exercises. Defines the structure and metadata of grammar quizzes.

| Column               | Type         | Constraints                             | Explanation                                            |
| -------------------- | ------------ | --------------------------------------- | ------------------------------------------------------ |
| `id`                 | UUID         | Primary Key                             | Unique assessment identifier                           |
| `title`              | VARCHAR(255) | NOT NULL                                | Assessment name (e.g., "Past Tense Basics")            |
| `topic`              | VARCHAR(255) | NULLABLE                                | Grammar topic (e.g., "verb_tenses", "articles")        |
| `total_questions`    | INTEGER      | NOT NULL, DEFAULT=0                     | Denormalized count of questions (for quick UI loading) |
| `time_limit_seconds` | INTEGER      | NULLABLE                                | Max allowed time to complete assessment                |
| `is_active`          | BOOLEAN      | NOT NULL, DEFAULT=TRUE                  | Whether assessment is available to users               |
| `created_at`         | TIMESTAMP    | NOT NULL, DEFAULT=NOW()                 | Assessment creation timestamp                          |
| `updated_at`         | TIMESTAMP    | NOT NULL, DEFAULT=NOW(), ONUPDATE=NOW() | Last modification timestamp                            |

**Why this table exists**:

- Acts as a reusable template for multiple users to attempt
- Separates content (assessments) from performance (attempts)
- Enables content management without affecting historical data

**Sample Row**:

```
id: 770e8400-e29b-41d4-a716-446655440003
title: Past Tense Conjugation
topic: verb_tenses
total_questions: 10
time_limit_seconds: 600
is_active: true
created_at: 2024-01-10 09:00:00+00
updated_at: 2024-01-10 09:00:00+00
```

---

### 4. GRAMMAR_QUESTIONS Table

**Purpose**: Individual grammar questions belonging to an assessment. Defines the question text and scoring.

| Column          | Type         | Constraints                                             | Explanation                                           |
| --------------- | ------------ | ------------------------------------------------------- | ----------------------------------------------------- |
| `id`            | UUID         | Primary Key                                             | Unique question identifier                            |
| `assessment_id` | UUID         | Foreign Key (grammar_assessments.id), NOT NULL, INDEXED | Parent assessment; CASCADE delete ensures cleanup     |
| `question_text` | TEXT         | NOT NULL                                                | The actual question prompt                            |
| `sort_order`    | INTEGER      | NOT NULL                                                | Display order within assessment (1, 2, 3...)          |
| `points`        | NUMERIC(6,2) | NOT NULL, DEFAULT=1.00                                  | Points awarded for correct answer (supports decimals) |
| `created_at`    | TIMESTAMP    | NOT NULL, DEFAULT=NOW()                                 | Question creation timestamp                           |
| `updated_at`    | TIMESTAMP    | NOT NULL, DEFAULT=NOW(), ONUPDATE=NOW()                 | Last modification timestamp                           |

**Why this table exists**:

- Normalizes questions to enable reusability across assessments
- `sort_order` ensures consistent question sequence
- `points` allows variable scoring strategies

**Sample Row**:

```
id: 880e8400-e29b-41d4-a716-446655440004
assessment_id: 770e8400-e29b-41d4-a716-446655440003
question_text: Which is the correct past tense of "go"?
sort_order: 1
points: 2.50
created_at: 2024-01-10 09:05:00+00
updated_at: 2024-01-10 09:05:00+00
```

---

### 5. GRAMMAR_QUESTION_OPTIONS Table

**Purpose**: Multiple choice options for grammar questions. Contains both correct and incorrect options.

| Column        | Type      | Constraints                                           | Explanation                                 |
| ------------- | --------- | ----------------------------------------------------- | ------------------------------------------- |
| `id`          | UUID      | Primary Key                                           | Unique option identifier                    |
| `question_id` | UUID      | Foreign Key (grammar_questions.id), NOT NULL, INDEXED | Parent question; CASCADE delete for cleanup |
| `option_text` | TEXT      | NOT NULL                                              | The option content/answer choice            |
| `sort_order`  | INTEGER   | NOT NULL                                              | Display order (A, B, C, D = 1, 2, 3, 4)     |
| `is_correct`  | BOOLEAN   | NOT NULL, DEFAULT=FALSE                               | Marks the correct answer                    |
| `created_at`  | TIMESTAMP | NOT NULL, DEFAULT=NOW()                               | Option creation timestamp                   |
| `updated_at`  | TIMESTAMP | NOT NULL, DEFAULT=NOW(), ONUPDATE=NOW()               | Last modification timestamp                 |

**Why this table exists**:

- Separates options from questions for cleaner data structure
- Multiple options per question follows relational best practices
- `is_correct` flag enables automated grading

**Relationship**: One question has multiple options (1:N)

**Sample Rows**:

```
id: 990e8400-e29b-41d4-a716-446655440005
question_id: 880e8400-e29b-41d4-a716-446655440004
option_text: Went
sort_order: 1
is_correct: true
created_at: 2024-01-10 09:06:00+00

id: 990e8400-e29b-41d4-a716-446655440006
question_id: 880e8400-e29b-41d4-a716-446655440004
option_text: Goed
sort_order: 2
is_correct: false
created_at: 2024-01-10 09:06:00+00

id: 990e8400-e29b-41d4-a716-446655440007
question_id: 880e8400-e29b-41d4-a716-446655440004
option_text: Going
sort_order: 3
is_correct: false
created_at: 2024-01-10 09:06:00+00

id: 990e8400-e29b-41d4-a716-446655440008
question_id: 880e8400-e29b-41d4-a716-446655440004
option_text: Gone
sort_order: 4
is_correct: false
created_at: 2024-01-10 09:06:00+00
```

---

### 6. GRAMMAR_ATTEMPTS Table

**Purpose**: Records each user's attempt to complete a grammar assessment. Tracks attempt metadata and aggregate scoring.

| Column               | Type         | Constraints                                             | Explanation                                             |
| -------------------- | ------------ | ------------------------------------------------------- | ------------------------------------------------------- |
| `id`                 | UUID         | Primary Key                                             | Unique attempt identifier                               |
| `assessment_id`      | UUID         | Foreign Key (grammar_assessments.id), NOT NULL, INDEXED | Which assessment is being attempted                     |
| `user_id`            | UUID         | Foreign Key (users.id), NULLABLE, INDEXED               | User taking the test (NULL for anonymous)               |
| `user_email`         | VARCHAR(320) | NULLABLE, INDEXED                                       | Email snapshot for non-authenticated users              |
| `status`             | ENUM         | NOT NULL, DEFAULT='in_progress'                         | Current status: 'in_progress', 'submitted', 'evaluated' |
| `started_at`         | TIMESTAMP    | NOT NULL                                                | When user started the attempt                           |
| `submitted_at`       | TIMESTAMP    | NULLABLE                                                | When user submitted answers (NULL if in-progress)       |
| `total_questions`    | INTEGER      | NOT NULL, DEFAULT=0                                     | Total questions in assessment (denormalized)            |
| `answered_questions` | INTEGER      | NOT NULL, DEFAULT=0                                     | Number of questions the user answered                   |
| `correct_answers`    | INTEGER      | NOT NULL, DEFAULT=0                                     | Number of correct answers                               |
| `score`              | NUMERIC(6,2) | NOT NULL, DEFAULT=0.00                                  | Final score (e.g., 8.50 out of 10)                      |
| `created_at`         | TIMESTAMP    | NOT NULL, DEFAULT=NOW()                                 | Attempt creation timestamp                              |
| `updated_at`         | TIMESTAMP    | NOT NULL, DEFAULT=NOW(), ONUPDATE=NOW()                 | Last modification timestamp                             |

**Why this table exists**:

- Separates attempt metadata from individual answers
- Status tracking enables resumable attempts
- Denormalized fields (`total_questions`, `answered_questions`, `correct_answers`, `score`) optimize query performance
- Supports both authenticated and anonymous users
- Immutable timestamp fields provide audit trail

**Sample Row**:

```
id: aa0e8400-e29b-41d4-a716-446655440009
assessment_id: 770e8400-e29b-41d4-a716-446655440003
user_id: 550e8400-e29b-41d4-a716-446655440001
user_email: john.doe@example.com
status: submitted
started_at: 2024-01-20 14:00:00+00
submitted_at: 2024-01-20 14:10:30+00
total_questions: 10
answered_questions: 8
correct_answers: 7
score: 8.75
created_at: 2024-01-20 14:00:00+00
updated_at: 2024-01-20 14:10:30+00
```

---

### 7. GRAMMAR_ATTEMPT_ANSWERS Table

**Purpose**: Individual answer records for each question in an attempt. Stores what option user selected and whether it was correct.

| Column               | Type    | Constraints                                                   | Explanation                                   |
| -------------------- | ------- | ------------------------------------------------------------- | --------------------------------------------- |
| `id`                 | UUID    | Primary Key                                                   | Unique answer record identifier               |
| `attempt_id`         | UUID    | Foreign Key (grammar_attempts.id), NOT NULL, INDEXED          | Which attempt this answer belongs to          |
| `question_id`        | UUID    | Foreign Key (grammar_questions.id), NOT NULL, INDEXED         | Which question this answer addresses          |
| `selected_option_id` | UUID    | Foreign Key (grammar_question_options.id), NULLABLE, SET NULL | Which option user selected (NULL = no answer) |
| `is_correct`         | BOOLEAN | NULLABLE                                                      | True/False/NULL (NULL = pending evaluation)   |

**Why this table exists**:

- Stores granular answer data for detailed analytics and review
- Links attempt to questions to options (3-way relationship)
- `is_correct` enables performance analysis by question
- NULL `is_correct` indicates pending grading

**Relationship**: One attempt has multiple answers (1:N), and one question may have many answers from different attempts (1:N)

**Sample Rows**:

```
id: bb0e8400-e29b-41d4-a716-446655440010
attempt_id: aa0e8400-e29b-41d4-a716-446655440009
question_id: 880e8400-e29b-41d4-a716-446655440004
selected_option_id: 990e8400-e29b-41d4-a716-446655440005
is_correct: true

id: bb0e8400-e29b-41d4-a716-446655440011
attempt_id: aa0e8400-e29b-41d4-a716-446655440009
question_id: 880e8400-e29b-41d4-a716-446655440004
selected_option_id: NULL
is_correct: false
```

---

### 8-14. READING_ASSESSMENTS, READING_QUESTIONS, READING_QUESTION_OPTIONS, READING_ATTEMPTS, READING_ATTEMPT_ANSWERS Tables

**Purpose**: Identical structure to Grammar tables, but for reading comprehension exercises.

**Key Differences from Grammar**:

- `READING_ASSESSMENTS` includes `passage_text` (the passage users read that students answer questions about)
- All foreign keys and relationships follow the same pattern

**Sample Reading Assessment Row**:

```
id: cc0e8400-e29b-41d4-a716-446655440012
title: The Industrial Revolution
passage_text: "The Industrial Revolution began in Britain in the 18th century... [long passage text]"
total_questions: 5
time_limit_seconds: 900
is_active: true
created_at: 2024-01-12 10:00:00+00
```

---

### 15-21. LISTENING_ASSESSMENTS, LISTENING_QUESTIONS, LISTENING_QUESTION_OPTIONS, LISTENING_ATTEMPTS, LISTENING_ATTEMPT_ANSWERS Tables

**Purpose**: Identical structure to Grammar tables, but for listening comprehension exercises.

**Key Differences**:

- `LISTENING_ASSESSMENTS` includes:
  - `audio_url`: URL to audio file to be played
  - `audio_duration_seconds`: Length of audio in seconds
- Allows users to listen and answer questions based on audio content

**Sample Listening Assessment Row**:

```
id: dd0e8400-e29b-41d4-a716-446655440013
title: Business Meeting Dialogue
audio_url: https://cdn.example.com/audio/business-meeting-001.mp3
audio_duration_seconds: 180
total_questions: 6
time_limit_seconds: 1200
is_active: true
created_at: 2024-01-14 11:00:00+00
```

---

## Relationships & Foreign Keys

### 1:0..1 Relationships (One-to-Optional-One)

- **USERS** → **USER_PROFILES**: One user has zero or one profile
  - FK: `user_profiles.user_id` → `users.id` (UNIQUE constraint ensures 1:0..1)
  - Cascade delete: If user deleted, profile deleted

### 1:N Relationships (One-to-Many)

#### Grammar Domain:

- **GRAMMAR_ASSESSMENTS** → **GRAMMAR_QUESTIONS**: One assessment has many questions
  - FK: `grammar_questions.assessment_id`
  - Cascade delete: Assessment deletion removes all questions
- **GRAMMAR_QUESTIONS** → **GRAMMAR_QUESTION_OPTIONS**: One question has many options
  - FK: `grammar_question_options.question_id`
  - Cascade delete: Question deletion removes all options
- **GRAMMAR_ASSESSMENTS** → **GRAMMAR_ATTEMPTS**: One assessment has many attempts
  - Multiple users can attempt same assessment multiple times
  - FK: `grammar_attempts.assessment_id`
- **GRAMMAR_ATTEMPTS** → **GRAMMAR_ATTEMPT_ANSWERS**: One attempt has many answers
  - FK: `grammar_attempt_answers.attempt_id`
  - One answer per question per attempt

#### M:N Relationships (Many-to-Many via Junction Table)

- **USERS** ↔ **GRAMMAR_ASSESSMENTS**: Implicit M:N via GRAMMAR_ATTEMPTS
  - One user can attempt many assessments
  - One assessment can be attempted by many users

---

## Normalization Principles

### First Normal Form (1NF)

✅ **Satisfied**: All columns contain atomic (indivisible) values

- Example: `question_text` is a single TEXT field, not multiple sub-columns
- No repeating groups; options are in separate table, not as comma-separated values in question row

### Second Normal Form (2NF)

✅ **Satisfied**: Every non-key column is fully dependent on the entire primary key

- Example: In `GRAMMAR_ATTEMPT_ANSWERS`, `is_correct` depends on both `attempt_id` and `question_id`, not just one
- No partial dependencies; `option_text` fully depends on `option_id`

### Third Normal Form (3NF)

✅ **Satisfied**: No non-key column depends on another non-key column (no transitive dependencies)

- Example: `question_text` is stored in `GRAMMAR_QUESTIONS`, not repeated in `GRAMMAR_ATTEMPT_ANSWERS`
- Assessment metadata (`title`, `description`) stays in `GRAMMAR_ASSESSMENTS`, not duplicated in attempts

### Boyce-Codd Normal Form (BCNF)

✅ **Mostly Satisfied**: Every determinant is a candidate key

- All tables have `UUID` primary keys
- Foreign keys properly reference primary keys
- Note: Denormalization is intentional in some cases (see below)

---

## Index Strategy

| Table                      | Column          | Reason                                |
| -------------------------- | --------------- | ------------------------------------- |
| `users`                    | `email`         | Fast login lookups, unique constraint |
| `grammar_attempts`         | `user_id`       | Quick retrieval of user's attempts    |
| `grammar_attempts`         | `assessment_id` | Find all attempts for an assessment   |
| `grammar_attempts`         | `status`        | Filter by attempt status              |
| `grammar_questions`        | `assessment_id` | Load questions for assessment         |
| `grammar_question_options` | `question_id`   | Load options for question             |
| `grammar_attempt_answers`  | `attempt_id`    | Load answers for attempt              |
| `grammar_attempt_answers`  | `question_id`   | Analytics on question performance     |

---

## Data Integrity & Cascading

### Cascade Delete Rules

All assessments, questions, options, and attempts follow CASCADE delete:

- Delete `grammar_assessment` → deletes all `grammar_questions`, `grammar_question_options`, and `grammar_attempts`
- Delete `grammar_question` → deletes all `grammar_question_options` and related `grammar_attempt_answers`
- Delete `grammar_attempt` → deletes all `grammar_attempt_answers`

### Soft Deletes

- `users.is_active = false` instead of hard delete
- `*_assessments.is_active = false` to retire without deleting historical data

### Foreign Key Constraints

- `SET NULL`: `grammar_attempt_answers.selected_option_id` → if option deleted, answer shows no selection
- `CASCADE`: All parent-child relationships to maintain referential integrity
- `NOT NULL`: Key relationships that must always exist

---
