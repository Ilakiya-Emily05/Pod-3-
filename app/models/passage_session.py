from sqlalchemy import Column, ForeignKey, Integer

from app.config.database import Base


class PassageSession(Base):
    __tablename__ = "passage_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    passage_id = Column(Integer, ForeignKey("passages.id"))
