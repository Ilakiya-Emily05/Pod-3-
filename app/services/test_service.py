from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.ai_generator import AIGeneratorService
from app.agents.question_agent import QuestionAgent
from app.repositories.question_repo import QuestionRepository
from app.repositories.test_session_repo import TestSessionRepository
from app.repositories.user_answer_repo import UserAnswerRepository
from uuid import UUID
from app.schemas.test_session_schema import AnswerResponse, TestSessionResponse


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

    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.session_repo = TestSessionRepository(db)
        self.answer_repo = UserAnswerRepository(db)
        self.question_agent = QuestionAgent(self.question_repo, self.answer_repo, AIGeneratorService())

    def get_questions_by_topic(self, topic: str, subtopic: str):
        self.question_agent.ensure_questions(topic, subtopic, session_id=None)
        return self.question_repo.get_by_topic(topic, subtopic, self.LIMIT)

    def start_test(self, user_id: UUID) -> TestSessionResponse:
        first_topic = list(GRAMMAR_FLOW.keys())[0]
        first_subtopic = GRAMMAR_FLOW[first_topic][0]

        session = self.session_repo.create_session(user_id=user_id, topic=first_topic, subtopic=first_subtopic)
        return TestSessionResponse(
            session_id=session.id,
            current_topic=session.current_topic,
            current_subtopic=session.current_subtopic,
            status=session.status,
            total_questions_attended=session.total_questions,
            total_correct_answers=session.total_correct,
        )

    def get_next_question(self, session_id: int) -> QuestionResponse:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.status == "COMPLETED":
            raise HTTPException(status_code=400, detail="Practice completed")

        self.question_agent.ensure_questions(session.current_topic, session.current_subtopic, session_id)

        attempted_ids = self.answer_repo.get_attempted_question_ids(session_id)
        question = self.question_repo.get_random_question(session.current_topic, session.current_subtopic, attempted_ids)
        if not question:
            raise HTTPException(status_code=404, detail="No question available")

        return QuestionResponse(
            id=question.id,
            topic=question.topic,
            subtopic=question.subtopic,
            question_text=question.question_text,
            options=question.options,
        )

    def submit_answer(self, session_id: int, question_id: int, selected_answer: str) -> AnswerResponse:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        question = self.question_repo.get_question_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        is_correct = selected_answer.upper() == question.correct_answer.upper()
        self.answer_repo.create_user_answer(session_id=session_id, question_id=question_id, selected_answer=selected_answer, is_correct=is_correct)

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

        self.session_repo.update(session)

        return AnswerResponse(
            is_correct=is_correct,
            current_topic=session.current_topic,
            current_subtopic=session.current_subtopic,
            status=session.status,
            total_questions_attended=session.total_questions,
            total_correct_answers=session.total_correct,
        )

    def move_to_next_subtopic(self, session):
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

    def get_summary(self, session_id: int, user_id: int):
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: This session does not belong to you")

        accuracy = 0.0 if session.total_questions == 0 else round((session.total_correct / session.total_questions) * 100, 2)
        answers = self.answer_repo.get_answers_by_session(session_id)
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
        for (topic, subtopic), data in subtopic_map.items():
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
