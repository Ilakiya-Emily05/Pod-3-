from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.config.database import Base


class PassageSession(Base):
    __tablename__ = "passage_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    passage_id = Column(Integer, ForeignKey("passages.id"))
