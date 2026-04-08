# app/models/listening_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

class ListeningAttempt(Base):
    __tablename__ = "listening_attempts"

    id = Column(Integer, primary_key=True, index=True)
    passage = Column(Text, nullable=False)
    questions = Column(JSON)
    user_transcript = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    audio_filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)