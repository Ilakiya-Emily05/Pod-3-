from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.agents.ai_generator import AIGeneratorService
from app.agents.question_agent import QuestionAgent
from app.repositories.question_repo import QuestionRepository
from app.repositories.test_session_repo import TestSessionRepository
from app.repositories.user_answer_repo import UserAnswerRepository
from app.schemas.question_schema import QuestionResponse
from app.schemas.test_session_schema import AnswerResponse, TestSessionResponse

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.question import Question
    from app.models.test_session import TestSession

GRAMMAR_FLOW = {
    "nouns": ["common_nouns", "proper_nouns", "collective_nouns", "abstract_nouns"],
    "pronouns": ["personal_pronouns", "possessive_pronouns"],
    "verbs": ["action_verbs", "linking_verbs"],
    "adjectives": ["descriptive_adjectives"],
}

QUESTIONS_PER_SUBTOPIC = 5
PASS_SCORE = 3
TOTAL_SUBTOPICS = sum(len(v) for v in GRAMMAR_FLOW.values())


class TestService:
    LIMIT = 10

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.session_repo = TestSessionRepository(db)
        self.answer_repo = UserAnswerRepository(db)
        self.question_agent = QuestionAgent(
            self.question_repo, self.answer_repo, AIGeneratorService()
        )

    async def get_questions_by_topic(self, topic: str, subtopic: str) -> list[Question]:
        await self.question_agent.ensure_questions(topic, subtopic, session_id=None)
        return await self.question_repo.get_by_topic(topic, subtopic, self.LIMIT)

    async def start_test(self, user_id: UUID) -> TestSessionResponse:
        first_topic = next(iter(GRAMMAR_FLOW.keys()))
        first_subtopic = GRAMMAR_FLOW[first_topic][0]

        session = await self.session_repo.create_session(
            user_id=user_id, topic=first_topic, subtopic=first_subtopic
        )
        return TestSessionResponse(
            session_id=session.id,
            current_topic=session.current_topic,
            current_subtopic=session.current_subtopic,
            status=session.status,
            total_questions_attended=session.total_questions,
            total_correct_answers=session.total_correct,
        )

    async def get_next_question(self, session_id: UUID, user_id: UUID) -> QuestionResponse:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Unauthorized: This session does not belong to you"
            )

        if session.status == "COMPLETED":
            raise HTTPException(status_code=400, detail="Practice completed")

        await self.question_agent.ensure_questions(
            session.current_topic, session.current_subtopic, session_id
        )

        attempted_ids = await self.answer_repo.get_attempted_question_ids(session_id)
        question = await self.question_repo.get_random_question(
            session.current_topic, session.current_subtopic, attempted_ids
        )
        if not question:
            raise HTTPException(status_code=404, detail="No question available")

        return QuestionResponse(
            id=question.id,
            topic=question.topic,
            subtopic=question.subtopic,
            question_text=question.question_text,
            options=question.options,
        )

    async def submit_answer(
        self, session_id: UUID, question_id: UUID, selected_answer: str, user_id: UUID
    ) -> AnswerResponse:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Unauthorized: This session does not belong to you"
            )

        question = await self.question_repo.get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        is_correct = selected_answer.upper() == question.correct_answer.upper()
        await self.answer_repo.create_user_answer(
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )

        if is_correct:
            session.correct_count += 1
            session.total_correct += 1

        session.total_questions += 1
        session.question_index += 1

        if session.correct_count >= PASS_SCORE:
            session.passed_subtopics += 1
            session.completed_subtopics += 1
            self.move_to_next_subtopic(session)
            session.question_index = 0
            session.correct_count = 0
        elif session.question_index >= QUESTIONS_PER_SUBTOPIC:
            session.failed_subtopics += 1
            session.completed_subtopics += 1
            self.move_to_next_subtopic(session)
            session.question_index = 0
            session.correct_count = 0

        if session.completed_subtopics >= TOTAL_SUBTOPICS:
            session.status = "COMPLETED"

        await self.session_repo.update(session)

        return AnswerResponse(
            is_correct=is_correct,
            current_topic=session.current_topic,
            current_subtopic=session.current_subtopic,
            status=session.status,
            total_questions_attended=session.total_questions,
            total_correct_answers=session.total_correct,
        )

    def move_to_next_subtopic(self, session: TestSession) -> None:
        topic = session.current_topic
        subtopics = GRAMMAR_FLOW[topic]
        index = subtopics.index(session.current_subtopic)

        if index < len(subtopics) - 1:
            session.current_subtopic = subtopics[index + 1]
            return

        topics = list(GRAMMAR_FLOW.keys())
        topic_index = topics.index(topic)

        if topic_index < len(topics) - 1:
            next_topic = topics[topic_index + 1]
            session.current_topic = next_topic
            session.current_subtopic = GRAMMAR_FLOW[next_topic][0]
        else:
            session.status = "COMPLETED"

    async def get_summary(self, session_id: UUID, user_id: UUID) -> dict[str, object]:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Unauthorized: This session does not belong to you"
            )

        accuracy = (
            0.0
            if session.total_questions == 0
            else round((session.total_correct / session.total_questions) * 100, 2)
        )
        answers = await self.answer_repo.get_answers_by_session(session_id)
        subtopic_map = {}

        for ans in answers:
            question = ans.question
            key = (question.topic, question.subtopic)
            if key not in subtopic_map:
                subtopic_map[key] = {"attempted": 0, "correct": 0}
            subtopic_map[key]["attempted"] += 1
            if ans.is_correct:
                subtopic_map[key]["correct"] += 1

        weak_topics = []
        strong_topics = []
        for (_topic, subtopic), data in subtopic_map.items():
            if data["correct"] >= PASS_SCORE:
                strong_topics.append(subtopic)
            else:
                weak_topics.append(subtopic)

        return {
            "session_id": session.id,
            "total_questions": session.total_questions,
            "total_correct": session.total_correct,
            "accuracy": accuracy,
            "passed_subtopics": session.passed_subtopics,
            "failed_subtopics": session.failed_subtopics,
            "completed_subtopics": session.completed_subtopics,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "status": session.status,
        }
