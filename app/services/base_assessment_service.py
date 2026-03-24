from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from uuid import UUID



class BaseAssessmentService:
    """Base service class for assessment-related operations.

    Provides common validation and scoring logic used across different assessment types
    (Grammar, Reading, Listening).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _validate_answers_input(
        self,
        answers: list[Any],
    ) -> set:
        """Validate that submitted answers don't have duplicate questions.

        Args:
            answers: List of submitted answers.

        Returns:
            Set of question IDs seen in the answers.

        Raises:
            ValueError: If a question appears multiple times in submitted answers.
        """
        seen_question_ids: set = set()
        for submitted in answers:
            if submitted.question_id in seen_question_ids:
                msg = f"Question {submitted.question_id} appears multiple times in submitted answers"
                raise ValueError(msg)
            seen_question_ids.add(submitted.question_id)
        return seen_question_ids

    def _validate_question_belongs_to_assessment(
        self,
        question_id: UUID,
        question_map: dict,
    ) -> Any:
        """Validate that a question belongs to the assessment.

        Args:
            question_id: The question ID to validate.
            question_map: Dictionary mapping question IDs to question objects.

        Returns:
            The question object.

        Raises:
            ValueError: If the question doesn't belong to the assessment.
        """
        question = question_map.get(question_id)
        if question is None:
            msg = f"Question {question_id} does not belong to this assessment"
            raise ValueError(msg)
        return question

    def _validate_option_for_question(
        self,
        selected_option_id: UUID | None,
        question: Any,
    ) -> bool | None:
        """Validate that the selected option is valid for the question.

        Args:
            selected_option_id: The selected option ID (can be None for unanswered).
            question: The question object.

        Returns:
            Whether the selected option is correct (None if not answered).

        Raises:
            ValueError: If the option is invalid for the question.
        """
        if selected_option_id is None:
            return None

        selected_option = next(
            (option for option in question.options if option.id == selected_option_id),
            None,
        )
        if selected_option is None:
            msg = (
                f"Option {selected_option_id} is invalid for question {question.id}"
            )
            raise ValueError(msg)
        return selected_option.is_correct

    def _calculate_score_for_answer(
        self,
        is_correct: bool | None,
        question: Any,
    ) -> tuple[int, Decimal]:
        """Calculate the score contribution for a single answer.

        Args:
            is_correct: Whether the answer is correct (None if unanswered).
            question: The question object.

        Returns:
            Tuple of (correct_count, score_amount). correct_count is 1 or 0,
            score_amount is the points value or Decimal("0.00").
        """
        if is_correct:
            return 1, question.points
        return 0, Decimal("0.00")

