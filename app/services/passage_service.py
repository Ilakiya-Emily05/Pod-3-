import asyncio

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.repositories.passage_repo import PassageRepository
from app.services.passage_pool import MAX_POOL, MIN_POOL, LOW_BUFFER, fill_pool, take_random_passage_id
from app.schemas.passage_schema import (
    PassageAnswerRequest,
    PassageAnswerResponse,
    PassageQuestion,
    PassageResponse,
    PassageStartResponse,
    PassageSummaryResponse,
)


class PassageService:
    QUESTIONS_PER_PASSAGE = 5

    def __init__(self, db: Session):
        self.db = db
        self.repo = PassageRepository(db)

    async def start_reading(self, user_id: int, background_tasks: BackgroundTasks) -> PassageStartResponse:
        passage_id = take_random_passage_id()
        if not passage_id:
            await fill_pool(MIN_POOL)
            passage_id = take_random_passage_id()

        if not passage_id:
            raise HTTPException(status_code=503, detail="Passage pool is warming up. Try again shortly.")

        session = self.repo.create_passage_session(user_id=user_id, passage_id=passage_id)
        self.ensure_question_buffer(session.id, passage_id, background_tasks)
        return PassageStartResponse(session_id=session.id, status="IN_PROGRESS")

    def ensure_passages(self, background_tasks: BackgroundTasks) -> None:
        total_passages = self.repo.count_passages()
        if total_passages < MIN_POOL:
            background_tasks.add_task(fill_pool, MIN_POOL)

    def preload_passages(self, target_size: int) -> None:
        """Synchronously preload passages into the pool up to the target size."""
        asyncio.run(fill_pool(target_size))

    def ensure_question_buffer(self, session_id: int, passage_id: int, background_tasks: BackgroundTasks) -> None:
        total_questions = self.repo.count_questions_by_passage(passage_id)
        attempted_questions = self.repo.count_attempted_questions(session_id, passage_id)
        available_questions = total_questions - attempted_questions
        if total_questions < self.QUESTIONS_PER_PASSAGE or available_questions < LOW_BUFFER:
            background_tasks.add_task(fill_pool, MAX_POOL)

    def get_passage(self, session_id: int):
        session = self.repo.get_passage_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        passage = self.repo.get_passage_by_id(session.passage_id)
        if not passage:
            raise HTTPException(status_code=404, detail="Passage not found")

        return PassageResponse(session_id=session.id, passage=passage.text)

    def get_questions(self, session_id: int, background_tasks: BackgroundTasks) -> list[PassageQuestion]:
        session = self.repo.get_passage_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        questions = self.repo.get_questions_by_passage(session.passage_id, limit=self.QUESTIONS_PER_PASSAGE)
        if not questions:
            fresh_passage = self.repo.get_random_passage_with_questions(self.QUESTIONS_PER_PASSAGE)
            if fresh_passage:
                session.passage_id = fresh_passage.id
                self.repo.db.commit()
                questions = self.repo.get_questions_by_passage(fresh_passage.id, limit=self.QUESTIONS_PER_PASSAGE)

        self.ensure_question_buffer(session.id, session.passage_id, background_tasks)

        return [PassageQuestion(id=q.id, question_text=q.question, options=q.options) for q in questions]

    def submit_answer(self, answer: PassageAnswerRequest, user_id: int) -> PassageAnswerResponse:
        session = self.repo.get_passage_session(answer.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: This session does not belong to you")

        question = self.repo.get_question_by_id(answer.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        is_correct = answer.selected_answer.upper() == question.correct_answer.upper()
        self.repo.create_passage_answer(
            session_id=answer.session_id,
            question_id=answer.question_id,
            selected_answer=answer.selected_answer,
            is_correct=is_correct,
        )

        return PassageAnswerResponse(is_correct=is_correct, correct_answer=question.correct_answer)

    def get_summary(self, session_id: int) -> PassageSummaryResponse:
        answers = self.repo.get_answers_by_session(session_id)
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        accuracy = (correct / total * 100) if total > 0 else 0

        weak_areas = []
        strong_areas = []
        for answer in answers:
            question = self.repo.get_question_by_id(answer.question_id)
            if question:
                difficulty = getattr(question, 'difficulty', 'medium')
                if not answer.is_correct and difficulty not in weak_areas:
                    weak_areas.append(difficulty)
                elif answer.is_correct and difficulty not in strong_areas:
                    strong_areas.append(difficulty)

        return PassageSummaryResponse(
            session_id=session_id,
            total_questions=total,
            total_correct=correct,
            accuracy=round(accuracy, 2),
            status="COMPLETED",
            weak_areas=weak_areas,
            strong_areas=strong_areas,
        )
