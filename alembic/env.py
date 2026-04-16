import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config.database import Base
from app.config.settings import get_settings
from app.models.analytics.user_progress import UserModuleProgress  # noqa: F401
from app.models.analytics.user_streaks import UserStreaks  # noqa: F401
from app.models.assessment_status import AttemptStatus  # noqa: F401
from app.models.base import TimestampMixin  # noqa: F401
from app.models.grammar import (  # noqa: F401
    GrammarAssessment,
    GrammarAttempt,
    GrammarAttemptAnswer,
    GrammarQuestion,
    GrammarQuestionOption,
)
from app.models.learning_path import LearningPath, ModuleUnlock  # noqa: F401
from app.models.listening import (  # noqa: F401
    ListeningAssessment,
    ListeningAttempt,
    ListeningAttemptAnswer,
    ListeningQuestion,
    ListeningQuestionOption,
)
from app.models.listening1 import ListeningSession  # noqa: F401
from app.models.passage_session import PassageSession  # noqa: F401
from app.models.reading import (  # noqa: F401
    ReadingAssessment,
    ReadingAttempt,
    ReadingAttemptAnswer,
    ReadingQuestion,
    ReadingQuestionOption,
)
from app.models.test_session import TestSession  # noqa: F401
from app.models.user import User, UserProfile  # noqa: F401
from app.models.Vocab.user_vocabulary import UserVocabulary  # noqa: F401
from app.models.Vocab.vocabulary_list import VocabularyList  # noqa: F401
from app.models.Vocab.vocabulary_session import VocabularySession  # noqa: F401
from app.models.Vocab.vocabulary_word import VocabularyWord  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
database_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL") or settings.database_url
if database_url and "+asyncpg" in database_url:
    database_url = database_url.replace("+asyncpg", "+psycopg2")
if database_url:
    # Runtime uses asyncpg (ssl=require) while Alembic uses psycopg2 (sslmode=require).
    database_url = database_url.replace("?ssl=require", "?sslmode=require")
    database_url = database_url.replace("&ssl=require", "&sslmode=require")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
