from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.assessment_status import AttemptStatus
from app.models.grammar import (
    GrammarAssessment,
    GrammarAttempt,
    GrammarAttemptAnswer,
    GrammarQuestion,
    GrammarQuestionOption,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.grammar import (
        GrammarAssessmentCreate,
        GrammarAssessmentUpdate,
        GrammarAttemptAnswerCreate,
        GrammarAttemptCreate,
    )


class GrammarService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_attempt_for_response(self, attempt_id: UUID) -> GrammarAttempt | None:
        result = await self.db.execute(
            select(GrammarAttempt)
            .options(selectinload(GrammarAttempt.answers))
            .where(GrammarAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()

    async def create_assessment(self, payload: GrammarAssessmentCreate) -> GrammarAssessment:
        assessment = GrammarAssessment(
            title=payload.title,
            description=payload.description,
            instructions=payload.instructions,
            topic=payload.topic,
            total_questions=payload.total_questions,
            time_limit_seconds=payload.time_limit_seconds,
            is_active=payload.is_active,
        )

        for question_payload in payload.questions:
            question = GrammarQuestion(
                question_text=question_payload.question_text,
                sort_order=question_payload.sort_order,
                points=question_payload.points,
            )
            for option_payload in question_payload.options:
                question.options.append(
                    GrammarQuestionOption(
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
            msg = "Grammar assessment creation failed"
            raise RuntimeError(msg)
        return created_assessment

    async def list_assessments(self, *, is_active: bool | None = None) -> list[GrammarAssessment]:
        query = select(GrammarAssessment).options(
            selectinload(GrammarAssessment.questions).selectinload(GrammarQuestion.options)
        )
        if is_active is not None:
            query = query.where(GrammarAssessment.is_active == is_active)

        result = await self.db.execute(query.order_by(GrammarAssessment.created_at.desc()))
        return list(result.scalars().all())

    async def get_assessment(self, assessment_id: UUID) -> GrammarAssessment | None:
        result = await self.db.execute(
            select(GrammarAssessment)
            .options(
                selectinload(GrammarAssessment.questions).selectinload(GrammarQuestion.options)
            )
            .where(GrammarAssessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def update_assessment(
        self,
        assessment_id: UUID,
        payload: GrammarAssessmentUpdate,
    ) -> GrammarAssessment | None:
        assessment = await self.get_assessment(assessment_id)
        if assessment is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(assessment, field_name, value)

        await self.db.commit()
        return await self.get_assessment(assessment.id)

    async def create_attempt(self, payload: GrammarAttemptCreate) -> GrammarAttempt:
        assessment = await self.get_assessment(payload.assessment_id)
        if assessment is None:
            msg = "Grammar assessment not found"
            raise ValueError(msg)

        attempt = GrammarAttempt(
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
        created_attempt = await self._get_attempt_for_response(attempt.id)
        if created_attempt is None:
            msg = "Grammar attempt creation failed"
            raise RuntimeError(msg)
        return created_attempt

    async def submit_attempt(
        self,
        attempt_id: UUID,
        answers: list[GrammarAttemptAnswerCreate],
    ) -> GrammarAttempt | None:
        result = await self.db.execute(
            select(GrammarAttempt)
            .options(
                selectinload(GrammarAttempt.answers),
                selectinload(GrammarAttempt.assessment)
                .selectinload(GrammarAssessment.questions)
                .selectinload(GrammarQuestion.options),
            )
            .where(GrammarAttempt.id == attempt_id)
        )
        attempt = result.scalar_one_or_none()
        if attempt is None:
            return None

        for existing_answer in attempt.answers:
            await self.db.delete(existing_answer)
        await self.db.flush()

        questions = attempt.assessment.questions
        question_map = {question.id: question for question in questions}

        new_answers: list[GrammarAttemptAnswer] = []
        correct_answers = 0
        score = Decimal("0.00")

        for submitted in answers:
            question = question_map.get(submitted.question_id)
            if question is None:
                msg = f"Question {submitted.question_id} does not belong to this assessment"
                raise ValueError(msg)

            is_correct: bool | None = None
            if submitted.selected_option_id is not None:
                selected_option = next(
                    (
                        option
                        for option in question.options
                        if option.id == submitted.selected_option_id
                    ),
                    None,
                )
                if selected_option is None:
                    msg = (
                        f"Option {submitted.selected_option_id} is invalid "
                        f"for question {question.id}"
                    )
                    raise ValueError(msg)
                is_correct = selected_option.is_correct

            if is_correct:
                correct_answers += 1
                score += question.points

            new_answers.append(
                GrammarAttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_id=submitted.selected_option_id,
                    is_correct=is_correct,
                )
            )

        self.db.add_all(new_answers)

        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = datetime.now(UTC)
        attempt.answered_questions = len(new_answers)
        attempt.correct_answers = correct_answers
        attempt.total_questions = len(questions)
        attempt.score = score

        await self.db.commit()
        updated_attempt = await self._get_attempt_for_response(attempt.id)
        if updated_attempt is None:
            msg = "Grammar attempt submission failed"
            raise RuntimeError(msg)
        return updated_attempt
