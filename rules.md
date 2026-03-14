# Backend Structure & Coding Rules

> **Full Code rules, 30 non-negotiable coding standards, and command references live .** This file is a concise quick-reference only.

This backend uses FastAPI with a thin, layered layout. Follow these rules when adding or changing code.

## Folder Map
- `app/main.py` — app factory and router mounting. No business logic here.
- `app/config/` — settings (`settings.py`) and database session/base (`database.py`).
- `app/controllers/routes/` — API routers. One file per domain (e.g., `users.py`), use dependencies for db/session.
- `app/models/` — SQLAlchemy ORM models. Keep table definitions only.
- `app/schemas/` — Pydantic request/response models. Separate create/update/read shapes.
- `app/services/` — Business logic. Services take dependencies (e.g., db) and return domain objects/data.
- `app/utils/` — Small helpers or shared types (e.g., result envelopes).
- `requirements.txt` — Python deps. Add only what you use.
- `.env` — runtime configuration (copy from `.env.example`), never commit secrets.

## Coding Rules
1) **Routing**: Add new endpoints in a router module under `app/controllers/routes/`; register it in `app/controllers/router.py`.
2) **Schemas**: Define request/response schemas in `app/schemas/`; avoid using ORM models in responses directly.
3) **Models**: Put SQLAlchemy models in `app/models/`; keep them focused on persistence, not business logic.
4) **Services**: Put business logic in `app/services/`; routers should only orchestrate request parsing, calling services, and shaping responses.
5) **DB Access**: Use the `get_db` dependency from `app/config/database.py` for sessions; never create engines/sessions in routes.
6) **Settings**: Read config through `get_settings()`; do not hardcode environment-specific values.
7) **Validation**: Use Pydantic models for input validation; add field constraints where useful.
8) **Testing hooks**: Write code to be testable (pure functions/services), avoid global state beyond settings and the db engine.
9) **Naming**: Use snake_case for files and functions, PascalCase for classes, and keep route paths plural (`/users`, `/orders`).
10) **Docs**: Keep router tags and docstrings concise; update this file if the structure changes.

## Adding a New Feature (checklist)
1) Create/extend ORM model in `app/models/` (run migrations if applicable).
2) Add/adjust Pydantic schemas in `app/schemas/`.
3) Implement business logic in `app/services/`.
4) Expose routes in `app/controllers/routes/` and register in `app/controllers/router.py`.
5) Update `.env.example` if new settings are needed.
6) Add tests (preferred locations: `tests/` mirroring app modules).

# /lint

Run Ruff linting and formatting operations.

**Usage:** `/lint [check|fix|format|report]`

Default (no argument): runs the full pre-commit sequence (`fix` then `format`).

---

## What to do

Based on `$ARGUMENTS`, run the corresponding command. If no argument is provided, run the **full pre-commit sequence**.

---

### `check` — Lint only, no changes

Report all lint issues without modifying any files.

```bash
uv run ruff check .
```

Use this to audit before deciding whether to auto-fix.

---

### `fix` — Auto-fix lint issues

Fix all auto-fixable issues in-place.

```bash
uv run ruff check . --fix
```

Some issues require manual resolution (e.g., `ANN` annotations, complex `SIM` refactors). Ruff will report these separately as unfixable.

---

### `format` — Format code (like Black)

Apply Ruff's formatter to all Python files.

```bash
uv run ruff format .
```

To check without changing files:
```bash
uv run ruff format . --check
```

---

### `report` — Full diagnostic report

Show all issues with rule codes and explanations.

```bash
uv run ruff check . --show-source
```

---

### Full pre-commit sequence (default)

Always run in this order — fix before format to avoid reformatting code that will be changed again:

```bash
uv run ruff check . --fix && uv run ruff format .
```

---

## Common Rule Codes

| Code | Rule | Notes |
|---|---|---|
| `E501` | Line too long | Max 100 chars (set in pyproject.toml) |
| `F401` | Unused import | Remove or add to `__all__` |
| `F841` | Local variable assigned but never used | Remove or use `_` prefix |
| `I001` | Import order | Ruff auto-fixes this |
| `N803` | Argument name should be lowercase | Use snake_case |
| `UP007` | Use `X \| Y` instead of `Optional[X]` | Ruff auto-upgrades |
| `B008` | Function call in default arg | **Ignored** — FastAPI `Depends()` pattern |
| `S101` | `assert` detected | Only ignored in `tests/` |
| `ANN001` | Missing type annotation | All params must be typed |
| `ANN201` | Missing return type annotation | All functions must have return types |
| `SIM108` | Use ternary instead of if-else | Usually auto-fixable |
| `TCH001` | Move import into `TYPE_CHECKING` block | For type-only imports |
| `RUF100` | Unused `noqa` directive | Remove stale suppression comments |

---

## `noqa` Comment Etiquette

Use `# noqa: <CODE>` to suppress a specific rule on one line. Always include the rule code — never use bare `# noqa`.

```python
# Good — specific, with a reason comment
result = some_complex_expression  # noqa: SIM108 — readability over brevity here

# Bad — suppresses everything
result = some_complex_expression  # noqa
```

**Never add `noqa` comments to silence errors that should be fixed.** Use them only for intentional exceptions (e.g., `B008` for `Depends()` is already globally ignored in `pyproject.toml`).


# /migrate

Run Alembic database migration operations safely.

**Usage:** `/migrate <action>`

Actions: `generate`, `up`, `down`, `status`, `history`

---

## What to do

Based on `$ARGUMENTS`, run the corresponding migration operation below.

---

### `generate <message>`

Generate a new autogenerated migration from current model changes.

```bash
uv run alembic revision --autogenerate -m "<message>"
```

**After generating:**
1. Open the new file in `alembic/versions/`
2. Review the `upgrade()` function — confirm all expected table/column changes are present
3. Review the `downgrade()` function — confirm it correctly reverses `upgrade()`
4. Check for any tables or columns that should NOT be in the migration (e.g., from third-party packages)
5. Only apply after review: `uv run alembic upgrade head`

---

### `up`

Apply all pending migrations to the database.

```bash
uv run alembic upgrade head
```

To apply only one step at a time:
```bash
uv run alembic upgrade +1
```

---

### `down`

Roll back the most recent migration.

```bash
uv run alembic downgrade -1
```

**Safety rules:**
- Never run `downgrade base` (drops all tables) without explicit confirmation.
- Never downgrade a migration that has been applied in staging or production.
- After rolling back, fix the model/migration, then run `uv run alembic upgrade head` again.

---

### `status`

Show the current migration revision applied to the database.

```bash
uv run alembic current
```

---

### `history`

Show the full migration history with details.

```bash
uv run alembic history --verbose
```

---

## Safety Rules (always enforce)

1. **Never edit an applied migration.** If a migration has been run in any environment, create a new one for corrections. Editing applied migrations breaks the revision chain.
2. **Never run `alembic downgrade base`** without explicit user confirmation — it drops all tables.
3. **Always review autogenerated migrations** before applying. Alembic can miss renames or generate unexpected drops.
4. **`DATABASE_URL_SYNC`** (psycopg2) must be set in `.env` — Alembic's `env.py` uses the sync driver, not asyncpg.
5. **Commit migration files** to git immediately after generating — other developers need them.

---

## Troubleshooting

**`Can't locate revision`** — run `uv run alembic history` and check for gaps in the chain.

**`Target database is not up to date`** — run `uv run alembic upgrade head` first.

**`No changes detected`** — ensure new models are imported in `alembic/env.py` (or via `app/models/__init__.py`).

**`asyncpg` connection error in Alembic** — Alembic must use `DATABASE_URL_SYNC` (psycopg2), not `DATABASE_URL` (asyncpg).


# /new-feature

Scaffold a complete new feature domain end-to-end.

**Usage:** `/new-feature <domain>`

Example: `/new-feature products`

---

## What to do

Given the domain name `$ARGUMENTS`, complete **all 8 steps** below in order. Do not skip a step.

---

### Step 1 — ORM Model (`app/models/<domain>.py`)

Create a SQLAlchemy async-compatible ORM model:

```python
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base

class <Domain>(Base):
    __tablename__ = "<domain>s"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Add domain-specific columns here
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
```

- Import and register the model in `app/models/__init__.py` so Alembic detects it.

---

### Step 2 — Pydantic Schemas (`app/schemas/<domain>.py`)

Create three schema shapes:

```python
from pydantic import BaseModel, ConfigDict

class <Domain>Create(BaseModel):
    # input fields for creation

class <Domain>Update(BaseModel):
    # all fields Optional for partial updates

class <Domain>Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    # response fields
```

---

### Step 3 — Service (`app/services/<domain>_service.py`)

Implement async CRUD functions. Each function takes `db: AsyncSession` as its first argument:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.<domain> import <Domain>
from app.schemas.<domain> import <Domain>Create, <Domain>Update

async def create_<domain>(db: AsyncSession, data: <Domain>Create) -> <Domain>: ...
async def get_<domain>(db: AsyncSession, id: int) -> <Domain>: ...
async def list_<domain>s(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[<Domain>]: ...
async def update_<domain>(db: AsyncSession, id: int, data: <Domain>Update) -> <Domain>: ...
async def delete_<domain>(db: AsyncSession, id: int) -> None: ...
```

- Raise `HTTPException(status_code=404)` when entity is not found.

---

### Step 4 — Router (`app/controllers/routes/<domain>.py`)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.<domain> import <Domain>Create, <Domain>Read, <Domain>Update
from app.services import <domain>_service

router = APIRouter(prefix="/<domain>s", tags=["<domain>s"])

@router.get("/", response_model=list[<Domain>Read])
async def list_<domain>s(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await <domain>_service.list_<domain>s(db, skip, limit)

@router.post("/", response_model=<Domain>Read, status_code=201)
async def create_<domain>(data: <Domain>Create, db: AsyncSession = Depends(get_db)):
    return await <domain>_service.create_<domain>(db, data)

@router.get("/{id}", response_model=<Domain>Read)
async def get_<domain>(id: int, db: AsyncSession = Depends(get_db)):
    return await <domain>_service.get_<domain>(db, id)

@router.patch("/{id}", response_model=<Domain>Read)
async def update_<domain>(id: int, data: <Domain>Update, db: AsyncSession = Depends(get_db)):
    return await <domain>_service.update_<domain>(db, id, data)

@router.delete("/{id}", status_code=204)
async def delete_<domain>(id: int, db: AsyncSession = Depends(get_db)):
    await <domain>_service.delete_<domain>(db, id)
```

---

### Step 5 — Register Router (`app/controllers/router.py`)

Add to the existing aggregator:

```python
from app.controllers.routes.<domain> import router as <domain>_router

api_router.include_router(<domain>_router)
```

---

### Step 6 — Alembic Migration

```bash
uv run alembic revision --autogenerate -m "add <domain>s table"
```

Review the generated file in `alembic/versions/` — confirm it contains the correct `upgrade()` and `downgrade()` operations before applying.

```bash
uv run alembic upgrade head
```

---

### Step 7 — Tests

Create two test files:

**`tests/unit/test_<domain>_service.py`** — mock the DB session:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.<domain>_service import create_<domain>, get_<domain>
from app.schemas.<domain> import <Domain>Create

@pytest.mark.unit
async def test_create_<domain>_returns_model():
    db = AsyncMock()
    data = <Domain>Create(...)
    result = await create_<domain>(db, data)
    assert result is not None
```

**`tests/integration/test_<domain>_router.py`** — use `httpx.AsyncClient` with a test DB:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_create_<domain>(client: AsyncClient):
    response = await client.post("/<domain>s/", json={...})
    assert response.status_code == 201
```

---

### Step 8 — Lint & Format Pass

```bash
uv run ruff check . --fix && uv run ruff format .
uv run pytest tests/unit/ -v --cov=app/services --cov-report=term-missing
```

---

## Completion Checklist

Before considering this feature done, confirm every item:

- [ ] ORM model created and registered in `app/models/__init__.py`
- [ ] Three schemas defined (`Create`, `Update`, `Read`)
- [ ] Service with full async CRUD implemented
- [ ] Router with 5 standard endpoints (list, create, get, update, delete)
- [ ] Router registered in `app/controllers/router.py`
- [ ] Alembic migration generated and reviewed
- [ ] Unit tests cover all service functions
- [ ] Integration tests cover all router endpoints
- [ ] `uv run ruff check . --fix` passes with zero errors
- [ ] `uv run ruff format .` applied
- [ ] Coverage on `app/services/` is >= 80%
- [ ] `.env.example` updated if any new settings were added


# /test

Run pytest with coverage reporting.

**Usage:** `/test [unit|integration|path|fast|html]`

Default (no argument): runs the full test suite with coverage.

---

## What to do

Based on `$ARGUMENTS`, run the corresponding pytest command below. Always report:
1. Pass / fail counts
2. Coverage percentage for `app/services/` (must be ≥ 80%)
3. Any failing test names with their error output

---

### No argument — full suite

```bash
uv run pytest --cov=app --cov-report=term-missing -v
```

---

### `unit` — Unit tests only

Fast, no I/O, mocked DB.

```bash
uv run pytest tests/unit/ -v --cov=app/services --cov-report=term-missing
```

---

### `integration` — Integration tests only

Requires a running test database. Set `DATABASE_URL` to a test DB before running.

```bash
uv run pytest tests/integration/ -v --cov=app --cov-report=term-missing
```

---

### `path <test-path>` — Specific file or directory

```bash
uv run pytest <test-path> -v --cov=app --cov-report=term-missing
```

Example: `/test path tests/unit/test_users_service.py`

---

### `fast` — Skip slow tests

Excludes tests marked with `@pytest.mark.slow`.

```bash
uv run pytest -m "not slow" -v --cov=app --cov-report=term-missing
```

---

### `html` — HTML coverage report

Generates a browsable report in `htmlcov/`.

```bash
uv run pytest --cov=app --cov-report=html --cov-report=term-missing
```

After running, open `htmlcov/index.html` in a browser.

---

## Coverage Requirements

| Layer | Minimum |
|---|---|
| `app/services/` | **80%** (enforced — CI fails below this) |
| `app/controllers/` | 70% (target) |
| `app/models/` | 60% (target) |

Coverage is configured in `pyproject.toml` under `[tool.coverage.report]`.

---

## Test Markers

Mark tests with these decorators to categorise them:

```python
@pytest.mark.unit          # no I/O, fast
@pytest.mark.integration   # requires real DB
@pytest.mark.slow          # takes > 2 seconds
```

Run specific markers:
```bash
uv run pytest -m unit
uv run pytest -m "integration and not slow"
```

---

## Pre-Commit Checklist

Before pushing any branch, all three must pass:

```bash
# 1. Lint + format
uv run ruff check . --fix && uv run ruff format .

# 2. Type check
uv run mypy app/

# 3. Tests with coverage
uv run pytest --cov=app --cov-report=term-missing
```

If any step fails, fix the issues before pushing. Do not use `--no-verify` to bypass hooks.

---

## Troubleshooting

**`ScopeMismatch` error** — async tests need `asyncio_mode = "auto"` (already set in `pyproject.toml`).

**`fixture not found`** — check `tests/conftest.py` for shared fixtures (db session, test client).

**Coverage below 80%** — add unit tests for uncovered service functions. Check the `term-missing` output for specific uncovered lines.

**Import errors** — ensure `uv sync` has been run and the venv is activated (or use `uv run pytest`).



# Power Up API

> See `rules.md` for a concise reference. This file is the authoritative source.

---

## Project Overview

**Power Up API** is an async FastAPI backend serving a React Native mobile app and a React admin dashboard. It uses Azure Postgres as the primary database, Azure OpenAI (via LangChain) for AI features, and is deployed on Azure App Service.

### Tech Stack

| Layer | Tool |
|---|---|
| Runtime | Python 3.12 |
| Web framework | FastAPI (async) |
| Package manager | **UV** (never pip) |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| DB driver (async) | asyncpg |
| DB driver (sync/Alembic) | psycopg2-binary |
| Validation | Pydantic v2 |
| Settings | pydantic-settings |
| LLM | Azure OpenAI via LangChain (`langchain-openai`) |
| Linter/Formatter | Ruff |
| Testing | pytest + pytest-asyncio + pytest-cov |
| Auth | python-jose (JWT) + passlib |
| HTTP client | httpx |

---

## Folder Map

```
api-powerup/
├── run.sh                       # Start dev server (creates venv/, syncs deps, runs uvicorn)
├── app/
│   ├── main.py                  # App factory + Swagger UI + health check. NO business logic.
│   ├── config/
│   │   ├── settings.py          # Pydantic-settings Settings class
│   │   └── database.py          # Async engine, SessionLocal, Base, get_db()
│   ├── controllers/
│   │   ├── router.py            # Aggregates all domain routers
│   │   └── routes/              # ONE file per domain (e.g. users.py, health.py)
│   ├── models/                  # SQLAlchemy ORM models (table definitions only)
│   ├── schemas/                 # Pydantic request/response shapes
│   ├── services/                # Business logic; tested independently
│   └── utils/                   # Small shared helpers (result envelopes, etc.)
├── alembic/
│   ├── env.py                   # Uses DATABASE_URL_SYNC (psycopg2)
│   └── versions/
├── tests/
│   ├── unit/                    # Pure function / service tests (mock DB)
│   └── integration/             # Tests that hit a real test DB
├── rules.md                     # Concise coding rules (points here)
├── pyproject.toml               # Single source of truth for deps + tooling
├── .env.example                 # Full env contract (copy → .env)

```

---

## 30 Non-Negotiable Coding Rules

### Structure
1. **Every new endpoint** lives in `app/controllers/routes/<domain>.py` and is registered in `app/controllers/router.py`. Never add routes to `main.py`.
2. **Routers are thin**: parse request → call service → return response schema. No DB queries, no business logic in routers.
3. **Services own all business logic**. Services receive dependencies (db session, settings) as arguments. They return domain objects or raise `HTTPException`.
4. **Models are persistence-only**. No methods, no computed properties, no business logic in ORM models.
5. **Max 300 lines per file**. If a file approaches this, split by responsibility.

### Database
6. **Always use `get_db()`** from `app/config/database.py` for DB sessions. Never instantiate engines or sessions directly in routes or services.
7. **All DB operations are async** (`await session.execute(...)`, `await session.commit()`, etc.). Never use blocking SQLAlchemy calls.
8. **`DATABASE_URL`** uses `postgresql+asyncpg://` for runtime. **`DATABASE_URL_SYNC`** uses `postgresql+psycopg2://` for Alembic only.
9. **Never edit an applied migration**. If a migration was run in any environment, create a new one for corrections.
10. **Always run `alembic upgrade head`** after pulling changes that include new migration files.

### Configuration
11. **All config via `get_settings()`**. Never hardcode URLs, secrets, or environment-specific values.
12. **`.env` is never committed**. `.env.example` is the contract; keep it up-to-date when adding new settings.
13. **Settings are validated at startup** via Pydantic. The app must refuse to start if required env vars are missing.

### Schemas
14. **Never return ORM model objects from endpoints**. Always use a Pydantic response schema.
15. **Separate schemas for Create / Update / Read** (e.g., `UserCreate`, `UserUpdate`, `UserRead`). Do not reuse the same schema for input and output.
16. **Use `model_config = ConfigDict(from_attributes=True)`** on read schemas to support ORM → Pydantic conversion.

### Naming
17. **Files and functions**: `snake_case`. **Classes**: `PascalCase`. **Constants**: `UPPER_SNAKE_CASE`.
18. **Route paths are plural** (`/users`, `/orders`, `/health-checks`).
19. **Schema suffix convention**: `*Create`, `*Update`, `*Read`, `*Response`. Service functions: `create_*`, `get_*`, `update_*`, `delete_*`.

### Error Handling
20. **Raise `HTTPException`** with explicit `status_code` and `detail` from services. Never return error dicts.
21. **Use `422` for validation errors** (Pydantic handles automatically), `404` for not found, `409` for conflicts, `401`/`403` for auth.
22. **Never swallow exceptions silently**. Log then re-raise or convert to `HTTPException`.

### Type Annotations
23. **All function signatures must be fully typed** — parameters and return types. No `Any` unless absolutely unavoidable.
24. **Use `Optional[X]`** (or `X | None`) for nullable fields. Do not use bare `None` type hints.

### LLM Usage
25. **Always use `AzureChatOpenAI`** from `langchain_openai`. Never import `openai` SDK directly.
26. **Chain with the pipe operator** (`prompt | llm | parser`). Avoid calling `.run()` or `.predict()`.
27. **Use `.with_structured_output(Schema)`** for JSON responses from the LLM.
28. **All LLM calls are async** (`await chain.ainvoke(...)`).

### Testing
29. **Minimum 80% coverage on `app/services/`**. Coverage failures block CI.
30. **Unit tests mock the DB session**. Integration tests use a dedicated test database, never the dev/prod DB.

---

## UV Command Reference

The project virtual environment lives at **`venv/`** (enforced via `UV_PROJECT_ENVIRONMENT=venv` in `run.sh`). Always use `./run.sh` to start the server so the correct venv is used — never `.venv/`.

```bash
# Start the server (creates venv/ and installs deps if needed, then runs uvicorn)
./run.sh

# Install all deps (including dev) — fast no-op if already up-to-date
uv sync

# Add a runtime dependency
uv add <package>

# Add a dev-only dependency
uv add --group dev <package>

# Remove a dependency
uv remove <package>

# Run a command inside the venv
uv run <command>

# Update all deps to latest compatible versions
uv lock --upgrade

# Show installed packages
uv pip list
```

**Never use `pip install` or `pip freeze`.** The lockfile `uv.lock` must be committed.

---

## Ruff Command Reference

```bash
# Check for lint issues (no fixes)
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check . --fix

# Format code (like Black)
uv run ruff format .

# Check formatting without changing files
uv run ruff format . --check

# Full pre-commit sequence
uv run ruff check . --fix && uv run ruff format .
```

---

## Alembic Command Reference

```bash
# Generate a new migration (autogenerate from model changes)
uv run alembic revision --autogenerate -m "short description"

# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1

# Show current migration state
uv run alembic current

# Show full migration history
uv run alembic history --verbose
```

---

## Testing Commands

```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run only unit tests
uv run pytest tests/unit/ -v

# Run only integration tests
uv run pytest tests/integration/ -v

# Run a specific file
uv run pytest tests/unit/test_users_service.py -v

# Fast run (no slow-marked tests)
uv run pytest -m "not slow" -v

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

**Coverage requirement**: `app/services/` must stay above **80%**. `fail_under=80` is set in `pyproject.toml`.

---

## Azure OpenAI + LangChain Usage Pattern

```python
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from app.config.settings import get_settings

settings = get_settings()


def get_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        temperature=0,
    )


# Plain text chain
async def generate_summary(text: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Summarise the following text."),
        ("human", "{text}"),
    ])
    chain = prompt | get_llm() | StrOutputParser()
    return await chain.ainvoke({"text": text})


# Structured output chain
class ExtractedData(BaseModel):
    name: str
    category: str

async def extract_data(raw: str) -> ExtractedData:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract structured data from the text."),
        ("human", "{raw}"),
    ])
    chain = prompt | get_llm().with_structured_output(ExtractedData)
    return await chain.ainvoke({"raw": raw})
```

---

## Conventional Commits Standard

Format: `<type>(<scope>): <subject>`

### Types
| Type | When to use |
|---|---|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `refactor` | Code change that isn't a fix or feature |
| `test` | Adding or fixing tests |
| `chore` | Tooling, deps, config changes |
| `docs` | Documentation only |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |

### Scopes (this codebase)
`auth`, `users`, `health`, `db`, `config`, `migrations`, `llm`, `schemas`, `services`, `router`, `tests`, `deps`, `ci`

### Examples
```
feat(users): add password reset endpoint
fix(auth): refresh token not invalidated on logout
chore(deps): upgrade langchain to 0.3
test(services): add coverage for user creation edge cases
refactor(db): extract session factory to config module
```

---

## NEVER DO

- **Never `pip install`** anything. Use `uv add` / `uv sync`.
- **Never import `openai` directly**. Use `langchain_openai.AzureChatOpenAI`.
- **Never return ORM objects from endpoints**. Always use a Pydantic response schema.
- **Never hardcode secrets, URLs, or env-specific values** in source code.
- **Never create sessions or engines** outside `app/config/database.py`.
- **Never write business logic in routers**. Delegate to services.
- **Never edit an applied migration**. Create a new one.
- **Never commit `.env`**. Only `.env.example`.
- **Never use `Any` in type hints** unless truly unavoidable (document why).
- **Never skip ruff + tests** before pushing. They are mandatory, not optional.
