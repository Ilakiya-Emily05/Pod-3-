
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.config.database import Base

class PronunciationResult(Base):
    __tablename__ = "pronunciation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)

    reference_text = Column(String, nullable=False)
    transcript = Column(String, nullable=False)
    pronunciation_score = Column(Float, nullable=False)
    total_mistakes = Column(Integer, default=0)
    mistakes = Column(JSON, nullable=True)
    improvement_tips = Column(JSON, nullable=True)
    audio_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())