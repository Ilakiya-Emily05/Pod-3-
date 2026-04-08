from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Disable echo to reduce noise
    future=True,
    poolclass=NullPool,  # Use NullPool to avoid connection pooling issues
)


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():  # noqa: ANN201
    """Dependency for providing a database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
