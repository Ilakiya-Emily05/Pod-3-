from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.config.database import Base


class ListeningAttempt(Base):
    __tablename__ = "listening_attempts"
    __table_args__ = {"extend_existing": True}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    passage = Column(Text, nullable=False)
    questions = Column(JSON)
    user_transcript = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    audio_filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
