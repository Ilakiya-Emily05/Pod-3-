# Branch Strategy — Sprint 4

## Rules
1. Always branch from `qa` 
2. Branch naming: `feature/{your-name}-s4-{short-desc}` (e.g., `feature/vishvaa-s4-assessment-session-api`)
3. PRs target `dev` first — Deepak reviews
4. After review: Deepak merges `dev` → `qa` 
5. Never push directly to `qa`, `dev`, or `main` 
6. Every PR must pass CI (lint + type check + tests)

## Commit format
`<type>(<scope>): <subject>` 
Types: feat | fix | refactor | test | chore | docs | perf | ci
Example: `feat(assessment): add session start endpoint` 

## PR checklist
- [ ] Branched from latest `qa` 
- [ ] All new files follow naming conventions (CLAUDE.md)
- [ ] Pydantic schemas: separate Create/Update/Read
- [ ] No ORM objects returned from endpoints
- [ ] No hardcoded secrets or URLs
- [ ] Tests pass locally
- [ ] ClickUp task ID in PR description

## CI/CD Pipeline
All PRs to `dev` branch will automatically run:
- `uv sync` (install dependencies)
- `uv run ruff check .` (linting)
- `uv run ruff format . --check` (formatting check)
- `uv run mypy app/` (type checking)
- `uv run pytest tests/unit/ -v --cov=app/services --cov-fail-under=80` (tests with coverage)

PRs will be blocked from merging if any step fails.
