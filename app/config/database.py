from collections.abc import AsyncGenerator

from sqlalchemy import text
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
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        )
        await connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'user_profiles'
                          AND column_name = 'dob'
                          AND data_type <> 'date'
                    ) THEN
                        ALTER TABLE user_profiles
                        ALTER COLUMN dob TYPE DATE
                        USING CASE
                            WHEN dob ~ '^\\d{2}/\\d{2}/\\d{4}$' THEN to_date(dob, 'DD/MM/YYYY')
                            ELSE dob::date
                        END;
                    END IF;
                END $$;
                """
            )
        )
