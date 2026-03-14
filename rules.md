# Backend Structure & Coding Rules

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