from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, create_async_engine as async_create_engine
from sqlalchemy.orm import DeclarativeBase, declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings


# ✅ Define Base class - SINGLE instance
class Base(DeclarativeBase):
    pass


# ✅ Engine with NullPool to avoid connection issues
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Disable echo to reduce noise
    future=True,
    poolclass=NullPool,  # Use NullPool to avoid connection pooling issues
)

# ✅ Session Factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """Dependency for providing a database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
