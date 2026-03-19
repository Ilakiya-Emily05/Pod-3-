from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.progress import UserProgress
from app.schemas.progress import ProgressComplete, ProgressStart


class ProgressController:
    """Controller for user progress tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_module(self, data: ProgressStart) -> UserProgress:
        """Start or resume a learning module."""
        # Check if progress already exists
        query = select(UserProgress).where(
            UserProgress.user_id == data.user_id,
            UserProgress.module_type == data.module_type,
            UserProgress.module_id == data.module_id,
        )
        result = await self.db.execute(query)
        existing_progress = result.scalar_one_or_none()

        if existing_progress:
            # Resume existing progress
            return existing_progress

        # Create new progress record
        new_progress = UserProgress(
            user_id=data.user_id,
            module_type=data.module_type,
            module_id=data.module_id,
            status="in_progress",
            started_at=datetime.utcnow(),
        )

        self.db.add(new_progress)
        await self.db.commit()
        await self.db.refresh(new_progress)

        return new_progress

    async def complete_module(
        self, user_id: UUID, module_type: str, module_id: UUID, data: ProgressComplete
    ) -> UserProgress:
        """Mark a module as completed with score."""
        query = select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.module_type == module_type,
            UserProgress.module_id == module_id,
        )
        result = await self.db.execute(query)
        progress = result.scalar_one_or_none()

        if not progress:
            # Create new progress record if doesn't exist
            progress = UserProgress(
                user_id=user_id,
                module_type=module_type,
                module_id=module_id,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                score=data.score,
                total_questions=data.total_questions,
                correct_answers=data.correct_answers,
            )
            self.db.add(progress)
        else:
            # Update existing progress
            progress.status = "completed"
            progress.completed_at = datetime.utcnow()
            progress.score = data.score
            progress.total_questions = data.total_questions
            progress.correct_answers = data.correct_answers

        await self.db.commit()
        await self.db.refresh(progress)

        return progress

    async def get_user_progress(self, user_id: UUID) -> list[UserProgress]:
        """Get all progress records for a user."""
        query = (
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .order_by(UserProgress.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_progress_summary(self, user_id: UUID) -> dict:
        """Get summarized progress for a user."""
        # Total modules started
        total_query = select(func.count(UserProgress.id)).where(
            UserProgress.user_id == user_id
        )
        total_result = await self.db.execute(total_query)
        total_started = total_result.scalar() or 0

        # Total modules completed
        completed_query = select(func.count(UserProgress.id)).where(
            UserProgress.user_id == user_id,
            UserProgress.status == "completed",
        )
        completed_result = await self.db.execute(completed_query)
        total_completed = completed_result.scalar() or 0

        # Average score (only for completed modules)
        avg_score_query = select(func.avg(UserProgress.score)).where(
            UserProgress.user_id == user_id,
            UserProgress.status == "completed",
            UserProgress.score.isnot(None),
        )
        avg_score_result = await self.db.execute(avg_score_query)
        avg_score = avg_score_result.scalar() or Decimal("0")

        # Modules by type
        type_query = select(
            UserProgress.module_type, func.count(UserProgress.id)
        ).where(
            UserProgress.user_id == user_id,
            UserProgress.status == "completed",
        )
        type_query = type_query.group_by(UserProgress.module_type)
        type_result = await self.db.execute(type_query)
        modules_by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_modules_started": total_started,
            "total_modules_completed": total_completed,
            "average_score": avg_score,
            "modules_by_type": modules_by_type,
        }
