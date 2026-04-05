from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.models import user  # noqa: F401
    async with engine.begin() as connection:
        try:
            await connection.run_sync(Base.metadata.create_all)
        except Exception:  # pragma: no cover - runtime DB mismatch (handled at runtime)
            import logging

            logging.exception(
                "Database initialization: failed to create tables. Likely schema mismatch with existing DB. Skipping create_all."
            )
