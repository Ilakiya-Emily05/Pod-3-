from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.sentence_framing import SentenceExercise, SentenceSubmission
from app.services.base_assessment_service import BaseAssessmentService
from app.services.cefr_grading_service import CEFRGradingService
from app.services.sentence_framing_ai_service import (
    evaluate_sentence_response,
    generate_sentence_exercise,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.sentence_framing import (
        SentenceGenerateRequest,
        SentenceSubmissionCreate,
    )

logger = logging.getLogger(__name__)

# Static Registry of Categories and Subcategories
# These UUIDs act as the 'exercise_id' trigger for dynamic generation
SENTENCE_CATEGORIES_REGISTRY = [
    {
        "category_id": "prof_emails",
        "name": "Professional Emails",
        "subcategories": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "Client Communication",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "name": "Manager Updates",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "name": "Team Coordination",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000004",
                "name": "Escalation Emails",
                "difficulty": "Adaptive",
            },
        ],
    },
    {
        "category_id": "report_writing",
        "name": "Report Writing",
        "subcategories": [
            {
                "id": "00000000-0000-0000-0000-000000000005",
                "name": "Status Reports",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000006",
                "name": "Incident Reports",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000007",
                "name": "Project Summaries",
                "difficulty": "Adaptive",
            },
        ],
    },
    {
        "category_id": "meeting_comm",
        "name": "Meeting Communication",
        "subcategories": [
            {
                "id": "00000000-0000-0000-0000-000000000008",
                "name": "Meeting Invites",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000009",
                "name": "Minutes Writing",
                "difficulty": "Adaptive",
            },
            {
                "id": "00000000-0000-0000-0000-000000000010",
                "name": "Follow-up",
                "difficulty": "Adaptive",
            },
        ],
    },
]


class SentenceFramingService(BaseAssessmentService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.grading_service = CEFRGradingService()

    async def get_categories(self) -> list[dict]:
        """Return the static list of categories and subcategories."""
        return SENTENCE_CATEGORIES_REGISTRY

    async def get_exercises_by_subcategory(self, subcategory: str) -> list[SentenceExercise]:
        """Return all exercises filtered by subcategory from the database."""
        result = await self.db.execute(
            select(SentenceExercise).where(SentenceExercise.subcategory == subcategory)
        )
        return list(result.scalars().all())

    def _get_subcategory_by_exercise_id(self, exercise_id: UUID) -> tuple[str, str] | None:
        """Finds the category and subcategory names for a given static UUID."""
        str_id = str(exercise_id)
        for cat in SENTENCE_CATEGORIES_REGISTRY:
            for sub in cat["subcategories"]:
                if sub["id"] == str_id:
                    return cat["name"], sub["name"]
        return None

    async def get_exercise(
        self, exercise_id: UUID, params: SentenceGenerateRequest | None = None
    ) -> SentenceExercise | None:
        """
        Generates a fresh AI exercise based on the subcategory linked to exercise_id.
        If params are provided, they override the defaults.
        """
        # 1. Identify subcategory from static registry
        mapping = self._get_subcategory_by_exercise_id(exercise_id)
        if not mapping:
            # Fallback: check if it's an existing exercise in DB (backward compat or submissions)
            result = await self.db.execute(
                select(SentenceExercise).where(SentenceExercise.id == exercise_id)
            )
            return result.scalar_one_or_none()

        cat_name, sub_name = mapping

        # 2. Trigger AI Generation
        # If params is None, use defaults
        cefr_level = params.cefr_level if params else "B1"
        difficulty = params.difficulty if params else "Professional"
        topic = params.topic if params else f"{cat_name}: {sub_name}"
        industry = params.industry if params else "General Professional"
        exercise_type = params.exercise_type if params else "fill_in_blank"

        ai_exercise = await generate_sentence_exercise(
            cefr_level=cefr_level,
            topic=topic,
            difficulty=difficulty,
            industry=industry,
            exercise_type=exercise_type,
        )

        if not ai_exercise:
            raise RuntimeError("Failed to generate exercise from AI")

        # 3. Create and Save to Database (as a new unique exercise instance)
        cefr_map = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}
        diff_score = cefr_map.get(ai_exercise.cefr_level.upper(), 3.0)

        exercise = SentenceExercise(
            category=cat_name,
            subcategory=sub_name,
            exercise_type=ai_exercise.exercise_type,
            difficulty=difficulty,
            cefr_level=ai_exercise.cefr_level,
            difficulty_score=diff_score,
            industry=industry,
            scenario=ai_exercise.scenario,
            context={
                "sender_role": ai_exercise.sender_role,
                "recipient": ai_exercise.recipient,
                "tone": ai_exercise.tone,
            },
            template=ai_exercise.template,
            hints=ai_exercise.hints,
            example_answer=ai_exercise.example_answer,
            time_limit_secs=300,
            points=10,
        )

        self.db.add(exercise)
        await self.db.commit()
        await self.db.refresh(exercise)
        return exercise

    async def submit_response(
        self, user_id: UUID, payload: SentenceSubmissionCreate
    ) -> SentenceSubmission:
        # We fetch the exact exercise instance created during generation
        stmt = select(SentenceExercise).where(SentenceExercise.id == payload.exercise_id)
        result = await self.db.execute(stmt)
        exercise = result.scalar_one_or_none()

        if not exercise:
            raise ValueError("Exercise not found")

        ai_eval = await evaluate_sentence_response(
            scenario=exercise.scenario,
            context=exercise.context,
            user_response=payload.response,
            exercise_type=exercise.exercise_type,
            difficulty=exercise.difficulty,
            cefr_level=exercise.cefr_level or "B1",
        )

        if not ai_eval:
            raise RuntimeError("Failed to evaluate response from AI")

        is_correct = ai_eval.overall_score >= 70
        grading_input = [
            {
                "cefr_level": exercise.cefr_level or "B1",
                "difficulty_score": float(exercise.difficulty_score or 3.0),
                "is_correct": is_correct,
            }
        ]

        history = await self._get_user_submission_history(user_id)
        grading_input.extend(history)

        grading_result = self.grading_service.grade(grading_input)

        submission = SentenceSubmission(
            user_id=user_id,
            exercise_id=exercise.id,
            response=payload.response,
            overall_score=ai_eval.overall_score,
            structure_score=ai_eval.structure_score,
            tone_score=ai_eval.tone_score,
            grammar_score=ai_eval.grammar_score,
            content_score=ai_eval.content_score,
            cefr_level=grading_result.cefr_level,
            ability_score=grading_result.ability_score,
            ai_feedback={
                "structure": {
                    "score": ai_eval.structure_score,
                    "comment": ai_eval.structure_comment,
                },
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
        await self.db.commit()
        await self.db.refresh(submission)

        return submission

    async def _get_user_submission_history(self, user_id: UUID) -> list[dict]:
        stmt = (
            select(SentenceSubmission, SentenceExercise)
            .join(SentenceExercise)
            .where(SentenceSubmission.user_id == user_id)
            .order_by(SentenceSubmission.submitted_at.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        history = []
        for submission, exercise in result.all():
            history.append(
                {
                    "cefr_level": exercise.cefr_level or "B1",
                    "difficulty_score": float(exercise.difficulty_score or 3.0),
                    "is_correct": submission.overall_score >= 70,
                }
            )
        return history

    async def get_user_progress(self, user_id: UUID) -> dict:
        result = await self.db.execute(
            select(SentenceSubmission)
            .where(SentenceSubmission.user_id == user_id)
            .order_by(SentenceSubmission.submitted_at.desc())
        )
        submissions = result.unique().scalars().all()

        if not submissions:
            return {"total_submissions": 0, "average_score": 0, "submissions": []}

        total_score = sum(s.overall_score for s in submissions)
        avg_score = total_score / len(submissions)

        return {
            "total_submissions": len(submissions),
            "average_score": round(avg_score, 2),
            "current_cefr_level": submissions[0].cefr_level if submissions else None,
            "submissions": [
                {
                    "submission_id": s.id,
                    "exercise_id": s.exercise_id,
                    "overall_score": s.overall_score,
                    "cefr_level": s.cefr_level,
                    "submitted_at": s.submitted_at,
                }
                for s in submissions
            ],
        }
