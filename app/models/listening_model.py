# app/models/listening_models.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from app.config.database import Base


class ListeningAttempt(Base):
    __tablename__ = "listening_attempts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    passage = Column(Text, nullable=False)
    questions = Column(JSON)
    user_transcript = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    audio_filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
