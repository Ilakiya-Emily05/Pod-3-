from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.assessment_status import AttemptStatus
from app.models.listening import (
    ListeningAssessment,
    ListeningAttempt,
    ListeningAttemptAnswer,
    ListeningQuestion,
    ListeningQuestionOption,
)
from app.services.base_assessment_service import BaseAssessmentService

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.listening import (
        ListeningAssessmentCreate,
        ListeningAssessmentUpdate,
        ListeningAttemptAnswerCreate,
        ListeningAttemptCreate,
    )


class ListeningService(BaseAssessmentService):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_attempt_for_response(
        self, attempt_id: UUID, user_id: UUID
    ) -> ListeningAttempt | None:
        """Fetch attempt by id and user_id to prevent information leakage.
        
        Returns None if attempt doesn't exist OR doesn't belong to the user.
        """
        result = await self.db.execute(
            select(ListeningAttempt)
            .options(selectinload(ListeningAttempt.answers))
            .where(ListeningAttempt.id == attempt_id, ListeningAttempt.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_assessment(self, payload: ListeningAssessmentCreate) -> ListeningAssessment:
        assessment = ListeningAssessment(
            title=payload.title,
            description=payload.description,
            instructions=payload.instructions,
            audio_url=payload.audio_url,
            audio_duration_seconds=payload.audio_duration_seconds,
            total_questions=payload.total_questions,
            time_limit_seconds=payload.time_limit_seconds,
            is_active=payload.is_active,
        )

        for question_payload in payload.questions:
            question = ListeningQuestion(
                question_text=question_payload.question_text,
                sort_order=question_payload.sort_order,
                points=question_payload.points,
            )
            for option_payload in question_payload.options:
                question.options.append(
                    ListeningQuestionOption(
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
            msg = "Listening assessment creation failed"
            raise RuntimeError(msg)
        return created_assessment

    async def list_assessments(self, *, is_active: bool | None = None) -> list[ListeningAssessment]:
        query = select(ListeningAssessment).options(
            selectinload(ListeningAssessment.questions).selectinload(ListeningQuestion.options)
        )
        if is_active is not None:
            query = query.where(ListeningAssessment.is_active == is_active)

        result = await self.db.execute(query.order_by(ListeningAssessment.created_at.desc()))
        return list(result.scalars().all())

    async def get_assessment(self, assessment_id: UUID) -> ListeningAssessment | None:
        result = await self.db.execute(
            select(ListeningAssessment)
            .options(
                selectinload(ListeningAssessment.questions).selectinload(ListeningQuestion.options)
            )
            .where(ListeningAssessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def update_assessment(
        self,
        assessment_id: UUID,
        payload: ListeningAssessmentUpdate,
    ) -> ListeningAssessment | None:
        assessment = await self.get_assessment(assessment_id)
        if assessment is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(assessment, field_name, value)

        await self.db.commit()
        return await self.get_assessment(assessment.id)

    async def create_attempt(self, payload: ListeningAttemptCreate) -> ListeningAttempt:
        assessment = await self.get_assessment(payload.assessment_id)
        if assessment is None:
            msg = "Listening assessment not found"
            raise ValueError(msg)

        attempt = ListeningAttempt(
            assessment_id=payload.assessment_id,
            user_id=payload.user_id,
            user_email=payload.user_email,
            started_at=payload.started_at,
            status=AttemptStatus.IN_PROGRESS,
            total_questions=assessment.total_questions,
            answered_questions=0,
            correct_answers=0,
            score=Decimal("0.00"),
        )

        self.db.add(attempt)
        await self.db.commit()
        created_attempt = await self._get_attempt_for_response(attempt.id, payload.user_id)
        if created_attempt is None:
            msg = "Listening attempt creation failed"
            raise RuntimeError(msg)
        return created_attempt

    async def submit_attempt(
        self,
        attempt_id: UUID,
        answers: list[ListeningAttemptAnswerCreate],
        user_id: UUID,
    ) -> ListeningAttempt | None:
        # Query with both attempt_id and user_id to enforce ownership at DB level
        # Returns None if attempt doesn't exist OR doesn't belong to the user
        result = await self.db.execute(
            select(ListeningAttempt)
            .options(
                selectinload(ListeningAttempt.answers),
                selectinload(ListeningAttempt.assessment)
                .selectinload(ListeningAssessment.questions)
                .selectinload(ListeningQuestion.options),
            )
            .where(ListeningAttempt.id == attempt_id, ListeningAttempt.user_id == user_id)
        )
        attempt = result.scalar_one_or_none()
        if attempt is None:
            return None

        # Validate that the attempt is in a submittable status
        if attempt.status != AttemptStatus.IN_PROGRESS:
            msg = f"Cannot submit attempt with status '{attempt.status}'. Only attempts with status 'in_progress' can be submitted."
            raise ValueError(msg)

        # Validate that submitted answers don't have duplicates BEFORE deleting
        self._validate_answers_input(answers)

        # Build question map for validation
        questions = attempt.assessment.questions
        question_map = {question.id: question for question in questions}

        # Validate all questions and options BEFORE deleting existing answers
        for submitted in answers:
            self._validate_question_belongs_to_assessment(
                submitted.question_id, question_map
            )
            self._validate_option_for_question(
                submitted.selected_option_id, question_map[submitted.question_id]
            )

        # Delete existing answers only after all validations pass
        for existing_answer in attempt.answers:
            await self.db.delete(existing_answer)
        await self.db.flush()

        # Process answers and calculate score
        new_answers: list[ListeningAttemptAnswer] = []
        correct_answers = 0
        score = Decimal("0.00")

        for submitted in answers:
            # Retrieve question and calculate score
            question = question_map[submitted.question_id]

            # Validate option and get correctness
            is_correct = self._validate_option_for_question(
                submitted.selected_option_id, question
            )

            # Calculate score contribution
            answer_correct_count, answer_score = self._calculate_score_for_answer(
                is_correct, question
            )
            correct_answers += answer_correct_count
            score += answer_score

            new_answers.append(
                ListeningAttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_id=submitted.selected_option_id,
                    is_correct=is_correct,
                )
            )

        self.db.add_all(new_answers)

        # Update attempt with submission results
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = datetime.now(UTC)
        attempt.answered_questions = len(new_answers)
        attempt.correct_answers = correct_answers
        attempt.total_questions = len(questions)
        attempt.score = score

        await self.db.commit()
        updated_attempt = await self._get_attempt_for_response(attempt.id, user_id)
        if updated_attempt is None:
            msg = "Listening attempt submission failed"
            raise RuntimeError(msg)
        return updated_attempt
