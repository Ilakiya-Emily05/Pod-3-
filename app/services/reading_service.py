from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.assessment_status import AttemptStatus
from app.models.reading import (
    ReadingAssessment,
    ReadingAttempt,
    ReadingAttemptAnswer,
    ReadingQuestion,
    ReadingQuestionOption,
)
from app.services.base_assessment_service import BaseAssessmentService
from app.services.cefr_grading_service import CEFRGradingService

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.reading import (
        ReadingAssessmentCreate,
        ReadingAssessmentUpdate,
        ReadingAttemptAnswerCreate,
        ReadingAttemptCreate,
    )


class ReadingService(BaseAssessmentService):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.grading_service = CEFRGradingService()

    async def _get_attempt_for_response(
        self, attempt_id: UUID, user_id: UUID
    ) -> ReadingAttempt | None:
        """Fetch attempt by id and user_id to prevent information leakage.

        Returns None if attempt doesn't exist OR doesn't belong to the user.
        """
        result = await self.db.execute(
            select(ReadingAttempt)
            .options(selectinload(ReadingAttempt.answers))
            .where(ReadingAttempt.id == attempt_id, ReadingAttempt.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_assessment(self, payload: ReadingAssessmentCreate) -> ReadingAssessment:
        assessment = ReadingAssessment(
            title=payload.title,
            passage_text=payload.passage_text,
            total_questions=payload.total_questions,
            time_limit_seconds=payload.time_limit_seconds,
            is_active=payload.is_active,
        )

        for question_payload in payload.questions:
            question = ReadingQuestion(
                question_text=question_payload.question_text,
                sort_order=question_payload.sort_order,
                points=question_payload.points,
                cefr_level=question_payload.cefr_level,
                difficulty_score=question_payload.difficulty_score,
            )
            for option_payload in question_payload.options:
                question.options.append(
                    ReadingQuestionOption(
                        option_text=option_payload.option_text,
                        sort_order=option_payload.sort_order,
                        is_correct=option_payload.is_correct,
                    )
                )
            assessment.questions.append(question)

        if payload.questions:
            assessment.total_questions = len(payload.questions)

        self.db.add(assessment)
        await self.db.commit()
        created_assessment = await self.get_assessment(assessment.id)
        if created_assessment is None:
            msg = "Reading assessment creation failed"
            raise RuntimeError(msg)
        return created_assessment

    async def list_assessments(self, *, is_active: bool | None = None) -> list[ReadingAssessment]:
        query = select(ReadingAssessment).options(
            selectinload(ReadingAssessment.questions).selectinload(ReadingQuestion.options)
        )
        if is_active is not None:
            query = query.where(ReadingAssessment.is_active == is_active)

        result = await self.db.execute(query.order_by(ReadingAssessment.created_at.desc()))
        return list(result.scalars().all())

    async def get_assessment(self, assessment_id: UUID) -> ReadingAssessment | None:
        result = await self.db.execute(
            select(ReadingAssessment)
            .options(
                selectinload(ReadingAssessment.questions).selectinload(ReadingQuestion.options)
            )
            .where(ReadingAssessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def update_assessment(
        self,
        assessment_id: UUID,
        payload: ReadingAssessmentUpdate,
    ) -> ReadingAssessment | None:
        assessment = await self.get_assessment(assessment_id)
        if assessment is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(assessment, field_name, value)

        await self.db.commit()
        return await self.get_assessment(assessment.id)

    async def create_attempt(self, payload: ReadingAttemptCreate) -> ReadingAttempt:
        assessment = await self.get_assessment(payload.assessment_id)
        if assessment is None:
            msg = "Reading assessment not found"
            raise ValueError(msg)

        attempt = ReadingAttempt(
            assessment_id=payload.assessment_id,
            user_id=payload.user_id,
            user_email=payload.user_email,
            started_at=payload.started_at,
            status=AttemptStatus.IN_PROGRESS,
            total_questions=assessment.total_questions,
            answered_questions=0,
            correct_answers=0,
            ability_score=None,
            cefr_level=None,
        )

        self.db.add(attempt)
        await self.db.commit()
        created_attempt = await self._get_attempt_for_response(attempt.id, payload.user_id)
        if created_attempt is None:
            msg = "Reading attempt creation failed"
            raise RuntimeError(msg)
        return created_attempt

    async def submit_attempt(
        self,
        attempt_id: UUID,
        answers: list[ReadingAttemptAnswerCreate],
        user_id: UUID,
    ) -> ReadingAttempt | None:
        # Query with both attempt_id and user_id to enforce ownership at DB level
        # Returns None if attempt doesn't exist OR doesn't belong to the user
        result = await self.db.execute(
            select(ReadingAttempt)
            .options(
                selectinload(ReadingAttempt.answers),
                selectinload(ReadingAttempt.assessment)
                .selectinload(ReadingAssessment.questions)
                .selectinload(ReadingQuestion.options),
            )
            .where(ReadingAttempt.id == attempt_id, ReadingAttempt.user_id == user_id)
        )
        attempt = result.scalar_one_or_none()
        if attempt is None:
            return None

        # Validate that the attempt is in a submittable status
        if attempt.status != AttemptStatus.IN_PROGRESS:
            msg = (
                f"Cannot submit attempt with status '{attempt.status}'. "
                "Only attempts with status 'in_progress' can be submitted."
            )
            raise ValueError(msg)

        # Validate that submitted answers don't have duplicates BEFORE deleting
        self._validate_answers_input(answers)

        # Build question map for validation
        questions = attempt.assessment.questions
        question_map = {question.id: question for question in questions}

        # Validate all questions and options BEFORE deleting existing answers
        for submitted in answers:
            self._validate_question_belongs_to_assessment(submitted.question_id, question_map)
            self._validate_option_for_question(
                submitted.selected_option_id, question_map[submitted.question_id]
            )

        # Delete existing answers only after all validations pass
        for existing_answer in attempt.answers:
            await self.db.delete(existing_answer)
        await self.db.flush()

        # Process answers and collect CEFR grading inputs
        new_answers: list[ReadingAttemptAnswer] = []
        grading_attempts: list[dict] = []
        correct_answers = 0

        for submitted in answers:
            # Retrieve question and validate CEFR metadata
            question = question_map[submitted.question_id]
            if question.cefr_level is None:
                msg = f"Question {question.id} is missing CEFR level"
                raise ValueError(msg)
            if question.difficulty_score is None:
                msg = f"Question {question.id} is missing difficulty score"
                raise ValueError(msg)

            # Validate option and get correctness
            is_correct = self._validate_option_for_question(submitted.selected_option_id, question)

            # Maintain count for existing response metadata
            answer_correct_count = 1 if is_correct else 0
            correct_answers += answer_correct_count

            grading_attempts.append(
                {
                    "cefr_level": question.cefr_level,
                    "difficulty_score": float(question.difficulty_score),
                    "is_correct": bool(is_correct),
                }
            )

            new_answers.append(
                ReadingAttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_id=submitted.selected_option_id,
                    is_correct=is_correct,
                    cefr_level=question.cefr_level,
                    difficulty_score=question.difficulty_score,
                )
            )

        self.db.add_all(new_answers)

        grading_result = self.grading_service.grade(grading_attempts)

        # Update attempt with submission results
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = datetime.now(UTC)
        attempt.answered_questions = len(new_answers)
        attempt.correct_answers = correct_answers
        attempt.total_questions = len(questions)
        attempt.ability_score = grading_result.ability_score
        attempt.cefr_level = grading_result.cefr_level

        await self.db.commit()
        updated_attempt = await self._get_attempt_for_response(attempt.id, user_id)
        if updated_attempt is None:
            msg = "Reading attempt submission failed"
            raise RuntimeError(msg)
        return updated_attempt
