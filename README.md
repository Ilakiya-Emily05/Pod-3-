# Power Up API

Async FastAPI backend for the Power Up platform — serving the React Native mobile app and React admin dashboard.

Built with Python 3.12 · FastAPI · SQLAlchemy (async) · Azure Postgres · Azure OpenAI via LangChain · UV

---

## Quick Start

### Prerequisites

| Tool | Install |
|---|---|
| Python 3.12 | `brew install python@3.12` |
| UV | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| PostgreSQL | Azure Postgres or local `brew install postgresql@16` |

### 1. Clone the repo

```bash
git clone <repo-url>
cd api-powerup
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your values — at minimum:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/powerup_db
DATABASE_URL_SYNC=postgresql+psycopg2://user:password@localhost:5432/powerup_db
SECRET_KEY=your-long-random-secret-key
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 3. Start the server

```bash
./run.sh
```

`run.sh` handles everything automatically:
- Creates `venv/` if it does not exist
- Installs / syncs all dependencies (fast no-op if already up-to-date)
- Copies `.env.example → .env` if `.env` is missing
- Starts uvicorn with hot-reload

```
🚀  Starting Power Up API on http://0.0.0.0:9000
    Swagger UI → http://localhost:9000/docs
    ReDoc      → http://localhost:9000/redoc
    Health     → http://localhost:9000/health
```

### 4. Run database migrations

```bash
UV_PROJECT_ENVIRONMENT=venv uv run alembic upgrade head
```

---

## API Documentation

| URL | Description |
|---|---|
| `http://localhost:9000/docs` | Swagger UI — interactive API explorer |
| `http://localhost:9000/redoc` | ReDoc — clean reference documentation |
| `http://localhost:9000/openapi.json` | Raw OpenAPI 3 schema |
| `http://localhost:9000/health` | Liveness probe |

---

## Development

### Dependency management

```bash
# Install all deps (runtime + dev)
UV_PROJECT_ENVIRONMENT=venv uv sync

# Add a new runtime dependency
UV_PROJECT_ENVIRONMENT=venv uv add <package>

# Add a dev-only dependency
UV_PROJECT_ENVIRONMENT=venv uv add --group dev <package>
```

Never use `pip install`. UV is the only package manager for this project.

### Linting & formatting

```bash
UV_PROJECT_ENVIRONMENT=venv uv run ruff check . --fix && uv run ruff format .
```

### Running tests

```bash
# Full suite with coverage
UV_PROJECT_ENVIRONMENT=venv uv run pytest --cov=app --cov-report=term-missing

# Unit tests only
UV_PROJECT_ENVIRONMENT=venv uv run pytest tests/unit/ -v

# Integration tests only
UV_PROJECT_ENVIRONMENT=venv uv run pytest tests/integration/ -v
```

Minimum required coverage on `app/services/`: **80%**

### Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async runtime connection (asyncpg driver) |
| `DATABASE_URL_SYNC` | Alembic migrations only (psycopg2 driver) |
| `SECRET_KEY` | JWT signing key |
| `AZURE_OPENAI_*` | Azure OpenAI credentials and deployment names |
| `DEBUG` | Enable debug mode (`true` / `false`) |
| `DOCS_ENABLED` | Show Swagger/ReDoc in production (`true` / `false`) |

Full contract in [`.env.example`](.env.example).

---

## Branching Policy

> **This policy is mandatory for all contributors. No exceptions.**

### Branch map

```
qa  (default, protected)
│
└── development  (protected)
│
└── feature/<ticket>-short-description   ← created from qa
    bugfix/<ticket>-short-description
    hotfix/<ticket>-short-description
    chore/<ticket>-short-description
```

### The two permanent branches

| Branch | Role | Direct push | PR target from feature |
|---|---|---|---|
| `qa` | Default branch · staging environment · source of truth | **Blocked** | Yes — after development sign-off |
| `development` | Integration environment · automated tests run here | **Blocked** | Yes — first PR destination |

### Workflow — step by step

```
1.  Checkout qa (always start from the freshest baseline)
    git checkout qa && git pull origin qa

2.  Create your feature branch FROM qa
    git checkout -b feature/PU-123-add-user-auth

3.  Develop, commit using Conventional Commits
    feat(auth): add JWT login endpoint

4.  Push and open PR → development
    • Base branch: development
    • This triggers CI (lint, tests, coverage check)
    • At least 1 reviewer approval required
    • All CI checks must be green before merge

5.  QA team / stakeholder tests in the development environment
    • If issues are found, fix on the SAME feature branch, push again
    • The open PR to development updates automatically

6.  Once development is signed off, open a second PR from the SAME feature
    branch → qa
    • Base branch: qa
    • Reference the development PR in the description
    • At least 1 reviewer approval required
    • All CI checks must be green before merge

7.  After merge to qa, delete the feature branch
```

### Branch naming convention

```
feature/<ticket-id>-short-description     # new functionality
bugfix/<ticket-id>-short-description      # non-critical bug fix
hotfix/<ticket-id>-short-description      # urgent production fix
chore/<ticket-id>-short-description       # deps, tooling, config
```

Examples:
```
feature/PU-42-user-registration
bugfix/PU-87-token-expiry-edge-case
hotfix/PU-101-null-pointer-on-login
chore/PU-15-upgrade-langchain
```

### Rules enforced by GitHub branch protection

The following rules are configured on both `qa` and `development`:

- **Direct push is blocked** — all changes must come through a PR
- **PR requires at least 1 approved review** before merge
- **All status checks must pass** (lint, tests, coverage) before merge
- **Branches must be up-to-date** with the base branch before merge
- **Force-push is disabled**
- **Branch deletion is disabled** (for `qa` and `development`)
- **`qa` is the default branch** — all new clones check out `qa`

### What is NOT allowed

- Opening a PR directly between `development` and `qa` (i.e., merging development → qa wholesale) — each feature goes through its own PR
- Creating a feature branch from `development` — always branch from `qa`
- Committing directly to `qa` or `development`
- Force-pushing to any branch
- Merging without a passing CI run

---

## Project Structure

```
api-powerup/
├── run.sh                       # One-command dev server start
├── app/
│   ├── main.py                  # App factory, Swagger UI, health check
│   ├── config/
│   │   ├── settings.py          # Pydantic-settings config
│   │   └── database.py          # Async engine + get_db()
│   ├── controllers/
│   │   ├── router.py            # Aggregates all domain routers
│   │   └── routes/              # One file per domain
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response shapes
│   ├── services/                # Business logic (tested independently)
│   └── utils/                   # Shared helpers
├── alembic/                     # Database migrations
│   └── versions/
├── tests/
│   ├── unit/                    # Mocked, no I/O
│   └── integration/             # Real test DB
├── pyproject.toml               # Deps + tooling config
├── .env.example                 # Environment variable contract
└── CLAUDE.md                    # AI assistant rules and coding standards
```

---

## Commit Convention

Format: `<type>(<scope>): <subject>`

```
feat(users): add password reset endpoint
fix(auth): refresh token not invalidated on logout
chore(deps): upgrade langchain to 0.3
test(services): add coverage for user creation edge cases
```

Types: `feat` · `fix` · `refactor` · `test` · `chore` · `docs` · `perf` · `ci`

---

## Tech Stack

| Layer | Tool | Version |
|---|---|---|
| Language | Python | 3.12 |
| Framework | FastAPI | ≥ 0.115 |
| ORM | SQLAlchemy (async) | ≥ 2.0 |
| Migrations | Alembic | ≥ 1.13 |
| Validation | Pydantic v2 | ≥ 2.7 |
| LLM | LangChain + Azure OpenAI | ≥ 0.3 |
| Auth | python-jose + passlib | — |
| Linter | Ruff | ≥ 0.4 |
| Tests | pytest + pytest-asyncio | — |
| Package manager | UV | — |
