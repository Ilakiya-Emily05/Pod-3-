from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.config.database import Base


class Passage(Base):
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
