from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.sentence_framing import SentenceExercise, SentenceSubmission
from app.services.base_assessment_service import BaseAssessmentService
from app.services.sentence_framing_ai_service import (
    evaluate_sentence_response,
)

if TYPE_CHECKING:
    from uuid import UUID
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.schemas.sentence_framing import (
        SentenceSubmissionCreate,
    )


class SentenceFramingService(BaseAssessmentService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_categories(self) -> list[dict]:
        """Return categories and subcategories dynamically from the database."""
        result = await self.db.execute(
            select(
                SentenceExercise.category, 
                SentenceExercise.subcategory, 
                SentenceExercise.difficulty
            ).distinct()
        )
        rows = result.all()
        
        categories_map = {}
        for cat_name, sub_name, diff in rows:
            if cat_name not in categories_map:
                categories_map[cat_name] = {
                    "category_id": cat_name.lower().replace(" ", "_"),
                    "name": cat_name,
                    "subcategories": []
                }
            
            # Check if subcategory already added (could have different difficulties, 
            # but usually one per subcategory in our seeding)
            if not any(s["name"] == sub_name for s in categories_map[cat_name]["subcategories"]):
                categories_map[cat_name]["subcategories"].append({
                    "id": sub_name, # Using name as ID for easier discovery
                    "name": sub_name,
                    "difficulty": diff
                })
        
        return list(categories_map.values())

    async def get_exercises_by_subcategory(self, subcategory: str) -> list[SentenceExercise]:
        """Return all exercises for a specific subcategory."""
        result = await self.db.execute(
            select(SentenceExercise)
            .where(SentenceExercise.subcategory == subcategory)
        )
        return list(result.scalars().all())

    async def get_exercise(self, exercise_id: UUID) -> SentenceExercise | None:
        result = await self.db.execute(
            select(SentenceExercise).where(SentenceExercise.id == exercise_id)
        )
        return result.scalar_one_or_none()

    async def submit_response(
        self, user_id: UUID, payload: SentenceSubmissionCreate
    ) -> SentenceSubmission:
        exercise = await self.get_exercise(payload.exercise_id)
        if not exercise:
            msg = "Exercise not found"
            raise ValueError(msg)

        ai_eval = await evaluate_sentence_response(
            scenario=exercise.scenario,
            context=exercise.context,
            user_response=payload.response,
            exercise_type=exercise.exercise_type,
            difficulty=exercise.difficulty,
        )

        if not ai_eval:
            msg = "Failed to evaluate response from AI"
            raise RuntimeError(msg)

        submission = SentenceSubmission(
            user_id=user_id,
            exercise_id=exercise.id,
            response=payload.response,
            overall_score=ai_eval.overall_score,
            structure_score=ai_eval.structure_score,
            tone_score=ai_eval.tone_score,
            grammar_score=ai_eval.grammar_score,
            content_score=ai_eval.content_score,
            ai_feedback={
                "structure": {"score": ai_eval.structure_score, "comment": ai_eval.structure_comment},
                "tone": {"score": ai_eval.tone_score, "comment": ai_eval.tone_comment},
                "grammar": {
                    "score": ai_eval.grammar_score,
                    "comment": ai_eval.grammar_comment,
                    "corrections": ai_eval.grammar_corrections,
                },
                "content": {
                    "score": ai_eval.content_score,
                    "comment": ai_eval.content_comment,
                    "suggestions": ai_eval.content_suggestions,
                },
                "improved_version": ai_eval.improved_version,
            },
            time_taken_secs=payload.time_taken_secs,
        )

        self.db.add(submission)
        
        # Find next exercise ID logic
        next_exercise_id = await self._get_next_exercise_id(exercise)
        submission._next_exercise_id = next_exercise_id # Temporary attribute for schema mapping

        await self.db.commit()
        await self.db.refresh(submission)
        
        submission.next_exercise_id = next_exercise_id # Set it back after refresh if needed, 
        # or handle in schema validation alias. 
        # Actually, let's just return it in the schema.
        
        return submission

    async def _get_next_exercise_id(self, current_exercise: SentenceExercise) -> UUID | None:
        """Find the next exercise in the same subcategory in a deterministic order."""
        # Find next exercise ID sorted by ID for a predictable sequence
        result = await self.db.execute(
            select(SentenceExercise.id)
            .where(
                SentenceExercise.subcategory == current_exercise.subcategory,
                SentenceExercise.id > current_exercise.id
            )
            .order_by(SentenceExercise.id.asc())
            .limit(1)
        )
        next_id = result.scalar_one_or_none()
        
        # Fallback to the first exercise if we're at the end of the list
        if not next_id:
            result = await self.db.execute(
                select(SentenceExercise.id)
                .where(
                    SentenceExercise.subcategory == current_exercise.subcategory,
                    SentenceExercise.id != current_exercise.id
                )
                .order_by(SentenceExercise.id.asc())
                .limit(1)
            )
            next_id = result.scalar_one_or_none()
            
        return next_id

    async def get_user_progress(self, user_id: UUID) -> dict:
        result = await self.db.execute(
            select(SentenceSubmission)
            .where(SentenceSubmission.user_id == user_id)
            .order_by(SentenceSubmission.submitted_at.desc())
        )
        submissions = result.scalars().all()

        if not submissions:
            return {
                "total_submissions": 0,
                "average_score": 0,
                "submissions": [],
            }

        total_score = sum(s.overall_score for s in submissions)
        avg_score = total_score / len(submissions)

        return {
            "total_submissions": len(submissions),
            "average_score": round(avg_score, 2),
            "submissions": [
                {
                    "submission_id": s.id,
                    "exercise_id": s.exercise_id,
                    "overall_score": s.overall_score,
                    "submitted_at": s.submitted_at,
                }
                for s in submissions
            ],
        }
