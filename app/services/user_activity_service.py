<<<<<<< HEAD
import uuid
=======
from uuid import UUID

from sqlalchemy.orm import Session
>>>>>>> origin/development


class UserActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db

<<<<<<< HEAD
    def record_activity(self, user_id: "uuid.UUID") -> None:
        # Minimal implementation: placeholder for recording user activity.
        # Extend to persist activity events as needed.
=======
    def record_activity(self, user_id: UUID) -> None:
>>>>>>> origin/development
        return None
