from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.config.database import Base


class ListeningSession(Base):
    __tablename__ = "listening_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)  # UUID string
    passage = Column(Text, nullable=False)
    questions = Column(JSONB)
    user_transcript = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)
    audio_filename = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
