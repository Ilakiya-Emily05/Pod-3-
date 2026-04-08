# 📚 Vocabulary Module – Backend Documentation

## 🧠 Overview

The Vocabulary Module is designed to provide **adaptive, spaced-repetition-based learning** using the **SM-2 algorithm**. It combines:

* 📖 Pre-seeded vocabulary dataset (initial learning)
* 🤖 AI-generated words (dynamic expansion)
* 🔁 Spaced repetition (long-term retention)

---

# ⚙️ Core Concepts

---

## 🔁 SM-2 Algorithm (Spaced Repetition)

The system uses a simplified and improved version of the **SM-2 algorithm** (used in apps like Anki).

### 📌 Inputs

* `quality` (0–5): derived from user response

  * `"again"` → 1
  * `"hard"` → 3
  * `"medium"` → 4
  * `"easy"` → 5

---

## 🧮 Key Fields

| Field              | Description                   |
| ------------------ | ----------------------------- |
| `retention_score`  | Easiness factor (default 2.5) |
| `repetition_count` | Number of successful recalls  |
| `interval_days`    | Days until next review        |
| `next_review_date` | When to show again            |

---

## 🔄 Algorithm Flow

### ❌ If user fails (`quality < 3`)

* Reset:

  * `repetition_count = 0`
  * `interval_days = 1`
* Reduce easiness factor (min = 1.3)

---

### ✅ If user succeeds (`quality >= 3`)

| Repetition | Interval              |
| ---------- | --------------------- |
| 0 → 1      | 1 day                 |
| 1 → 2      | 6 days                |
| ≥2         | `interval × easiness` |

---

### ⚡ Adjustments

* `"hard"` → slows interval growth
* `"easy"` → boosts interval
* Easiness factor is clamped: **1.3 → 3.0**

---

## 🎯 Goal

Ensure:

* Frequently forgotten words appear more often
* Known words appear less frequently

---

# 🌱 Initial Data Seeding

---

## 📦 First Step: Seed 100 Words

Before AI kicks in, the system uses:

* ✅ 100 **unique vocabulary words**
* ✅ Mixed CEFR levels (A1 → B2)
* ✅ Industry context (default: IT)

---

## 🧠 Why Seed First?

* Avoid cold-start problem
* Ensure immediate usability
* Reduce dependency on AI

---

## 📌 Example Structure

```json
{
  "word": "stakeholder",
  "definition": "a person with interest in a project",
  "cefr_level": "B1",
  "example_sentence": "All stakeholders must approve the plan."
}
```

---

# 🤖 AI Word Generation (Threshold-Based)

---

## 🔥 When AI is Triggered

AI generation happens **only when needed**.

### Condition:

```text
If total words (per CEFR level) < threshold
```

---

## ⚙️ Threshold Logic

| Condition  | Action                 |
| ---------- | ---------------------- |
| Words ≥ 50 | Do nothing             |
| Words < 50 | Generate ~20 new words |

---

## 🧠 Flow

```text
GET /words →
    fetch due words →
    fetch new words →
    if not enough →
        trigger AI →
        store in DB →
        fetch again
```

---

## 📌 AI Responsibilities

* Generate:

  * word
  * definition
  * example sentence
* Filter invalid responses
* Persist to DB

---

# 🔁 Learning Flow

---

## 📥 Step 1: Fetch Words

```http
GET /vocabulary/words/{user_id}
```

Returns:

* Due words (based on SM-2)
* New words (if needed)
* AI-generated words (fallback)

---

## 🧠 Step 2: User Interaction

User selects:

```text
again | hard | medium | easy
```

---

## 📤 Step 3: Submit Response

```http
POST /vocabulary/response
```

System updates:

* SM-2 fields
* Next review schedule
* Learning status

---

# ⚠️ Important Design Decisions

---

## 🧠 1. Backend vs Frontend Responsibilities

| Backend          | Frontend                  |
| ---------------- | ------------------------- |
| SM-2 scheduling  | Immediate retry ("again") |
| Data persistence | UI flow                   |
| AI generation    | Queue handling            |

---

## 🔁 2. “Again” Behavior

* Backend → schedules future review
* Frontend → handles **immediate retry**

---

## 📦 3. Batch Fetching (limit = 10)

* Improves performance
* Reduces API calls
* Frontend shows one-by-one

---

## 🛡️ 4. Data Integrity

* Unique constraint: `(user_id, word_id)`
* Foreign keys enforced
* Status validation (`learning`, `mastered`, `struggling`)

---

## ⏱️ 5. Time Handling

* Uses **timezone-aware timestamps (UTC)**
* Prevents scheduling issues across regions

---

## 🚫 6. Input Validation

* Only accepts:

  ```text
  again, hard, medium, easy
  ```
* Invalid inputs → rejected

---

# 📊 Status System

| Status     | Condition           |
| ---------- | ------------------- |
| learning   | default             |
| mastered   | repetition ≥ 5      |
| struggling | incorrect > correct |

---

# 🚀 Production Notes

---

## ✅ Ready

* SM-2 logic correct
* AI fallback integrated
* Scalable structure
* Clean service separation

---

## ⚠️ Future Improvements

* Unit tests for SM-2
* Background AI generation
* CEFR progression per user
* Analytics dashboard

---

# 🏁 Summary

This module provides:

* 📚 Adaptive vocabulary learning
* 🔁 Proven spaced repetition (SM-2)
* 🤖 Intelligent content expansion via AI
* ⚡ Efficient and scalable backend design

---

> 💡 Designed for both **learning efficiency** and **system scalability**

---
