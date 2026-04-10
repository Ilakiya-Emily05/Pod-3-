from uuid import UUID

from sqlalchemy.orm import Session


class UserActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_activity(self, user_id: UUID) -> None:
        return None
