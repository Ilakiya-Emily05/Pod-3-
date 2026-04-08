from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    word_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    word: Mapped[str] = mapped_column(String(100), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String(20))
    
    # ✅ CEFR instead of basic/intermediate
    cefr_level: Mapped[str] = mapped_column(String(5))  # A1, A2, B1...

    industry: Mapped[str | None] = mapped_column(String(50))
    example_sentence: Mapped[str | None] = mapped_column(Text)
    pronunciation_audio_url: Mapped[str | None] = mapped_column(String(500))

    # 🔗 link to list
    list_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vocabulary_lists.list_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)