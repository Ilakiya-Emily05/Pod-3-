from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.models.base import Base as DatabaseBase

settings = get_settings()

engine_kwargs = {"echo": settings.debug, "future": True}
if "+asyncpg" in settings.database_url:
    # Cosmos/PgBouncer can reject reused prepared statements from asyncpg's default cache.
    engine_kwargs["connect_args"] = {"statement_cache_size": 0}

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = DatabaseBase


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Compatibility wrapper — some modules import `get_session`.

    Keeps older import name working while the codebase uses `get_db`.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.models import user  # noqa: F401
    from app.models.assessment_session import AssessmentSession  # noqa: F401
    from app.models.final_reports import FinalReport  # noqa: F401

    async with engine.begin() as connection:
        try:
            await connection.run_sync(Base.metadata.create_all)
        except Exception:  # pragma: no cover - runtime DB mismatch (handled at runtime)
            import logging

            logging.exception(
                "Database initialization: failed to create tables. Likely schema mismatch with existing DB. Skipping create_all."
            )