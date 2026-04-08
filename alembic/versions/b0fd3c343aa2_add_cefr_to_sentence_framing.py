"""add_cefr_to_sentence_framing

Revision ID: b0fd3c343aa2
Revises: 6cf5cdad4292
Create Date: 2026-04-06 15:20:29.652818

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b0fd3c343aa2"
down_revision: str | Sequence[str] | None = "6cf5cdad4292"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make this migration idempotent: it was generated on a branch that overlaps
    # with other CEFR-related migrations.
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE cefr_level_enum AS ENUM ('A1','A2','B1','B2','C1','C2'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='grammar_attempt_answers') THEN
            EXECUTE 'ALTER TABLE grammar_attempt_answers ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE grammar_attempt_answers ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='grammar_attempts') THEN
            EXECUTE 'ALTER TABLE grammar_attempts ADD COLUMN IF NOT EXISTS ability_score NUMERIC(6,4)';
            EXECUTE 'ALTER TABLE grammar_attempts ADD COLUMN IF NOT EXISTS cefr_level VARCHAR(3)';
            EXECUTE 'ALTER TABLE grammar_attempts DROP COLUMN IF EXISTS score';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='grammar_questions') THEN
            EXECUTE 'ALTER TABLE grammar_questions ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE grammar_questions ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='listening_attempt_answers') THEN
            EXECUTE 'ALTER TABLE listening_attempt_answers ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE listening_attempt_answers ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='listening_attempts') THEN
            EXECUTE 'ALTER TABLE listening_attempts ADD COLUMN IF NOT EXISTS ability_score NUMERIC(6,4)';
            EXECUTE 'ALTER TABLE listening_attempts ADD COLUMN IF NOT EXISTS cefr_level VARCHAR(3)';
            EXECUTE 'ALTER TABLE listening_attempts DROP COLUMN IF EXISTS score';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='listening_questions') THEN
            EXECUTE 'ALTER TABLE listening_questions ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE listening_questions ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='reading_attempt_answers') THEN
            EXECUTE 'ALTER TABLE reading_attempt_answers ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE reading_attempt_answers ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='reading_attempts') THEN
            EXECUTE 'ALTER TABLE reading_attempts ADD COLUMN IF NOT EXISTS ability_score NUMERIC(6,4)';
            EXECUTE 'ALTER TABLE reading_attempts ADD COLUMN IF NOT EXISTS cefr_level VARCHAR(3)';
            EXECUTE 'ALTER TABLE reading_attempts DROP COLUMN IF EXISTS score';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='reading_questions') THEN
            EXECUTE 'ALTER TABLE reading_questions ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE reading_questions ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='sentence_exercises') THEN
            EXECUTE 'ALTER TABLE sentence_exercises ADD COLUMN IF NOT EXISTS cefr_level cefr_level_enum';
            EXECUTE 'ALTER TABLE sentence_exercises ADD COLUMN IF NOT EXISTS difficulty_score NUMERIC(6,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='user_progress') THEN
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS honesty_humility DECIMAL(5,2)';
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS emotionality DECIMAL(5,2)';
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS extraversion DECIMAL(5,2)';
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS agreeableness DECIMAL(5,2)';
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS conscientiousness DECIMAL(5,2)';
            EXECUTE 'ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS openness DECIMAL(5,2)';
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='user_sentence_submissions') THEN
            EXECUTE 'ALTER TABLE user_sentence_submissions ADD COLUMN IF NOT EXISTS cefr_level VARCHAR(3)';
            EXECUTE 'ALTER TABLE user_sentence_submissions ADD COLUMN IF NOT EXISTS ability_score NUMERIC(6,4)';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE user_sentence_submissions DROP COLUMN IF EXISTS ability_score")
    op.execute("ALTER TABLE user_sentence_submissions DROP COLUMN IF EXISTS cefr_level")

    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS openness")
    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS conscientiousness")
    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS agreeableness")
    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS extraversion")
    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS emotionality")
    op.execute("ALTER TABLE user_progress DROP COLUMN IF EXISTS honesty_humility")

    op.execute("ALTER TABLE sentence_exercises DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE sentence_exercises DROP COLUMN IF EXISTS cefr_level")

    op.execute("ALTER TABLE reading_questions DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE reading_questions DROP COLUMN IF EXISTS cefr_level")
    op.execute(
        "ALTER TABLE reading_attempts ADD COLUMN IF NOT EXISTS score NUMERIC(6,2) NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE reading_attempts DROP COLUMN IF EXISTS cefr_level")
    op.execute("ALTER TABLE reading_attempts DROP COLUMN IF EXISTS ability_score")
    op.execute("ALTER TABLE reading_attempt_answers DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE reading_attempt_answers DROP COLUMN IF EXISTS cefr_level")

    op.execute("ALTER TABLE listening_questions DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE listening_questions DROP COLUMN IF EXISTS cefr_level")
    op.execute(
        "ALTER TABLE listening_attempts ADD COLUMN IF NOT EXISTS score NUMERIC(6,2) NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE listening_attempts DROP COLUMN IF EXISTS cefr_level")
    op.execute("ALTER TABLE listening_attempts DROP COLUMN IF EXISTS ability_score")
    op.execute("ALTER TABLE listening_attempt_answers DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE listening_attempt_answers DROP COLUMN IF EXISTS cefr_level")

    op.execute("ALTER TABLE grammar_questions DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE grammar_questions DROP COLUMN IF EXISTS cefr_level")
    op.execute(
        "ALTER TABLE grammar_attempts ADD COLUMN IF NOT EXISTS score NUMERIC(6,2) NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE grammar_attempts DROP COLUMN IF EXISTS cefr_level")
    op.execute("ALTER TABLE grammar_attempts DROP COLUMN IF EXISTS ability_score")
    op.execute("ALTER TABLE grammar_attempt_answers DROP COLUMN IF EXISTS difficulty_score")
    op.execute("ALTER TABLE grammar_attempt_answers DROP COLUMN IF EXISTS cefr_level")
