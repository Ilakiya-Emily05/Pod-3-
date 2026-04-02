# UUID Migration Status and Runbook

## Overview

This document summarizes the migration from legacy INT/String user identifiers to UUID across modules, what has already been completed, and what remains.

## Why UUID

- More secure: non-sequential and hard to guess.
- Better for distributed systems and cross-pod integrations.
- Matches Pod 1 baseline (`users.id` is UUID).
- Simplifies token identity (`sub`) and service-level joins.

## Migration Strategy Used

We used a phased migration to avoid breaking running services:

1. Add UUID columns in transition phase.
2. Backfill UUID values from legacy values.
3. Create mapping table for legacy numeric IDs.
4. Update code paths to use UUID.
5. Verify data and schema.
6. Finalize cutover (NOT NULL + drop legacy columns).

## What Was Done So Far

### 1) Pronunciation and Legacy Session Model UUID conversion

- Updated model columns from INT to UUID where required.
- Registered pronunciation model in centralized model imports for metadata discovery.

Code updates:

- app/models/pronunciation_model.py
- app/models/test_session.py
- app/models/passage_session.py
- app/models/**init**.py
- app/repository/pronounciation_repo.py
- app/routes/audio_route.py
- app/services/analytics_service.py

### 2) Initial DB migration for INT -> UUID columns

Migration:

- alembic/versions/c1d2e3f4a5b6_migrate_user_id_columns_to_uuid.py

Purpose:

- Convert `pronunciation_results.user_id` INT -> UUID.
- Convert `test_sessions.user_id` INT -> UUID.
- Convert `passage_sessions.user_id` INT -> UUID.
- Create `pronunciation_results` table if absent in Alembic-managed environments.

### 3) Pod 3 transition migration (UUID + mapping)

Migration:

- alembic/versions/d7f8a9b0c1d2_pod3_user_id_uuid_migration.py

Purpose:

- Add `uuid_user_id` to `key_skills` and `interview_sessions`.
- Create `user_id_mapping(legacy_int_id, uuid_id)`.
- Backfill UUID from:
  - UUID-like legacy `user_id` strings.
  - Numeric legacy `user_id` values via mapping table.
- Add indexes on `uuid_user_id`.

### 4) Pod 3 code refactor to UUID

Code updates:

- app/models/interview_system.py
- app/services/interview_service.py
- app/schemas/interview.py
- app/controllers/routes/practice.py
- app/controllers/routes/interview.py
- app/controllers/routes/resume.py
- app/services/analytics_service.py

### 5) Final Pod 3 cutover migration

Migration:

- alembic/versions/e4f5a6b7c8d9_finalize_pod3_uuid_cutover.py

Purpose:

- Enforce `uuid_user_id` as `NOT NULL`.
- Drop legacy `user_id` columns from:
  - `key_skills`
  - `interview_sessions`
- Drop legacy indexes on old `user_id`.
- Keep `user_id_mapping` table for post-cutover safety/auditing.

### 6) JWT contract standardization

Code updates:

- app/services/auth_service.py
- app/utils/auth.py

Token now follows this structure:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "student",
  "iat": 1711708800,
  "exp": 1711795200
}
```

## Migration Execution

Applied migrations up to head using:

- `uv run alembic upgrade head`

## Verification Performed

### Data verification pass

Executed checks for:

- total rows in `key_skills` / `interview_sessions`
- null `uuid_user_id` counts
- numeric/UUID legacy value classifications
- mapping coverage and orphan checks

Observed in current environment:

- `key_skills`: 0 rows
- `interview_sessions`: 0 rows
- null UUID rows: 0
- mapping rows: 0
- orphan mappings: 0

### Schema verification pass

Confirmed:

- `key_skills.uuid_user_id` exists, type UUID, NOT NULL
- `interview_sessions.uuid_user_id` exists, type UUID, NOT NULL
- legacy `user_id` columns removed from Pod 3 tables
- `ix_key_skills_uuid_user_id` and `ix_interview_sessions_uuid_user_id` present
- `user_id_mapping` table still present

## Current State Summary

- Pod 3 user identity is now UUID-first in DB and code.
- JWT identity contract is standardized and validated.
- Analytics path now consumes UUID-aligned identity sources.

## What Still Needs To Be Done

### High priority

1. Add integration tests for Pod 3 routes/services using UUID user IDs.
2. Run end-to-end flow tests:
   - resume upload -> keyword ingestion
   - practice question -> answer submit
   - mock interview session start/list/result
3. Verify production/staging data if those environments have non-empty Pod 3 tables.

### Medium priority

1. Decide retention period for `user_id_mapping` (for audit/rollback support).
2. Add a cleanup migration to drop `user_id_mapping` after stabilization.
3. Ensure all remaining legacy INT user_id signatures in older modules are migrated (test/passage/user activity paths).

### Analytics backlog

1. Implement and wire remaining endpoints:
   - `GET /api/v1/analytics/heatmap/{user_id}`
   - `GET /api/v1/analytics/trends/{user_id}?period=30d`
2. Confirm Pod 3 source of truth for:
   - overall score

- final reports

## Rollback Guidance

- Alembic downgrade is available for each migration, but data rollback from UUID to INT is not lossless for converted values.
- If rollback is required in shared environments, prefer DB snapshot restore over logical down-conversion.

## Recommended Next Step

- Keep current schema as-is for one stabilization sprint.
- During this period, monitor API logs and run scheduled integrity checks on UUID columns.
- After validation window, remove `user_id_mapping` with a dedicated cleanup migration.
