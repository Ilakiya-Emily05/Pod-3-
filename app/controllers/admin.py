from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.grammar import GrammarAssessment, GrammarAttempt
from app.models.listening import ListeningAssessment, ListeningAttempt
from app.models.reading import ReadingAssessment, ReadingAttempt
from app.models.user import User
from app.schemas.admin import QuestionCreate


class AdminController:
    """Admin controller for user management and analytics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_users(
        self, page: int = 1, page_size: int = 20, search: str | None = None
    ) -> dict:
        """Get paginated list of users with optional search."""
        # Total count
        total_query = select(func.count(User.id))
        if search:
            total_query = total_query.where(User.email.ilike(f"%{search}%"))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Paginated query
        query = select(User).options(selectinload(User.profile)).order_by(User.created_at.desc())
        if search:
            query = query.where(User.email.ilike(f"%{search}%"))

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = result.scalars().all()

        # Convert to dict format
        users_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "profile_completed": user.profile_completed,
                "created_at": user.created_at,
            }
            if user.profile:
                user_dict["profile"] = {
                    "name": user.profile.name,
                    "mobile": user.profile.mobile,
                    "college": user.profile.college,
                }
            users_data.append(user_dict)

        return {
            "users": users_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size),
        }

    async def get_analytics(self) -> dict:
        """Get platform-wide analytics."""
        # Total users
        total_users_query = select(func.count(User.id))
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0

        # Active users (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_query = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0

        # Total assessments
        reading_count = await self.db.execute(select(func.count(ReadingAssessment.id)))
        listening_count = await self.db.execute(select(func.count(ListeningAssessment.id)))
        grammar_count = await self.db.execute(select(func.count(GrammarAssessment.id)))
        total_assessments = (
            reading_count.scalar() + listening_count.scalar() + grammar_count.scalar() or 0
        )

        # Total attempts
        reading_attempts = await self.db.execute(select(func.count(ReadingAttempt.id)))
        listening_attempts = await self.db.execute(select(func.count(ListeningAttempt.id)))
        grammar_attempts = await self.db.execute(select(func.count(GrammarAttempt.id)))
        total_attempts = (
            reading_attempts.scalar() + listening_attempts.scalar() + grammar_attempts.scalar() or 0
        )

        # Average ability score (from all attempts)
        reading_attempt_count_query = select(func.count(ReadingAttempt.id)).where(
            ReadingAttempt.ability_score.isnot(None)
        )
        reading_attempt_count_result = await self.db.execute(reading_attempt_count_query)
        reading_attempt_count = reading_attempt_count_result.scalar() or 0

        listening_attempt_count_query = select(func.count(ListeningAttempt.id)).where(
            ListeningAttempt.ability_score.isnot(None)
        )
        listening_attempt_count_result = await self.db.execute(listening_attempt_count_query)
        listening_attempt_count = listening_attempt_count_result.scalar() or 0

        grammar_attempt_count_query = select(func.count(GrammarAttempt.id)).where(
            GrammarAttempt.ability_score.isnot(None)
        )
        grammar_attempt_count_result = await self.db.execute(grammar_attempt_count_query)
        grammar_attempt_count = grammar_attempt_count_result.scalar() or 0

        reading_ability_query = select(func.sum(ReadingAttempt.ability_score)).where(
            ReadingAttempt.ability_score.isnot(None)
        )
        reading_ability_result = await self.db.execute(reading_ability_query)
        reading_ability_total = reading_ability_result.scalar() or Decimal("0")

        listening_ability_query = select(func.sum(ListeningAttempt.ability_score)).where(
            ListeningAttempt.ability_score.isnot(None)
        )
        listening_ability_result = await self.db.execute(listening_ability_query)
        listening_ability_total = listening_ability_result.scalar() or Decimal("0")

        grammar_ability_query = select(func.sum(GrammarAttempt.ability_score)).where(
            GrammarAttempt.ability_score.isnot(None)
        )
        grammar_ability_result = await self.db.execute(grammar_ability_query)
        grammar_ability_total = grammar_ability_result.scalar() or Decimal("0")

        total_ability_sum = reading_ability_total + listening_ability_total + grammar_ability_total
        total_ability_attempts = (
            reading_attempt_count + listening_attempt_count + grammar_attempt_count
        )
        avg_score = (
            total_ability_sum / Decimal(total_ability_attempts)
            if total_ability_attempts > 0
            else Decimal("0")
        )

        # Module completion rate
        completed_query = select(func.count(User.id)).where(
            User.profile_completed == True  # noqa: E712
        )
        completed_result = await self.db.execute(completed_query)
        completed = completed_result.scalar() or 0
        completion_rate = (completed / total_users * 100) if total_users > 0 else 0

        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_query = select(func.count(User.id)).where(User.created_at >= seven_days_ago)
        recent_result = await self.db.execute(recent_query)
        recent_activity = {"last_7_days": recent_result.scalar() or 0}

        # CEFR distribution (placeholder - would need CEFR field in user profile)
        cefr_distribution = {
            "A1": 0,
            "A2": 0,
            "B1": 0,
            "B2": 0,
            "C1": 0,
            "C2": 0,
        }

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_assessments_created": total_assessments,
            "total_attempts": total_attempts,
            "average_user_score": avg_score,
            "cefr_distribution": cefr_distribution,
            "module_completion_rate": round(completion_rate, 2),
            "recent_activity": recent_activity,
        }

    async def create_question(self, data: QuestionCreate) -> dict:
        """Create a question for an assessment (admin only)."""
        if data.assessment_type == "reading":
            from app.models.reading import ReadingQuestion, ReadingQuestionOption

            question_class = ReadingQuestion
            option_class = ReadingQuestionOption
            assessment_class = ReadingAssessment
        elif data.assessment_type == "listening":
            from app.models.listening import ListeningQuestion, ListeningQuestionOption

            question_class = ListeningQuestion
            option_class = ListeningQuestionOption
            assessment_class = ListeningAssessment
        elif data.assessment_type == "grammar":
            from app.models.grammar import GrammarQuestion, GrammarQuestionOption

            question_class = GrammarQuestion
            option_class = GrammarQuestionOption
            assessment_class = GrammarAssessment
        else:
            raise ValueError(f"Invalid assessment type: {data.assessment_type}")

        # Verify assessment exists
        assessment_query = select(assessment_class).where(assessment_class.id == data.assessment_id)
        assessment_result = await self.db.execute(assessment_query)
        assessment = assessment_result.scalar_one_or_none()

        if not assessment:
            raise ValueError(f"Assessment {data.assessment_id} not found")

        # Create question
        question = question_class(
            assessment_id=data.assessment_id,
            question_text=data.question_text,
            sort_order=data.sort_order,
            points=float(data.points),
            cefr_level=data.cefr_level,
            difficulty_score=float(data.difficulty_score),
        )

        self.db.add(question)
        await self.db.flush()  # Get question ID

        # Create options
        for opt_data in data.options:
            option = option_class(
                question_id=question.id,
                option_text=opt_data["option_text"],
                sort_order=opt_data.get("sort_order", 1),
                is_correct=opt_data.get("is_correct", False),
            )
            self.db.add(option)

        await self.db.commit()
        await self.db.refresh(question)

        return {
            "id": question.id,
            "assessment_id": question.assessment_id,
            "question_text": question.question_text,
            "sort_order": question.sort_order,
            "points": question.points,
            "cefr_level": question.cefr_level,
            "difficulty_score": question.difficulty_score,
            "options": [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "sort_order": opt.sort_order,
                    "is_correct": opt.is_correct,
                }
                for opt in question.options
            ],
        }
