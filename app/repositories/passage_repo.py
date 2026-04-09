from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.passage import Passage
from app.models.passage_answer import PassageAnswer
from app.models.passage_question import ComprehensionQuestion
from app.models.passage_session import PassageSession


class PassageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_passage(self, text: str) -> Passage:
        passage = Passage(text=text)
        self.db.add(passage)
        self.db.commit()
        self.db.refresh(passage)
        return passage

    def get_passage_by_id(self, passage_id: int) -> Passage | None:
        return self.db.query(Passage).filter(Passage.id == passage_id).first()

    def get_random_passage(self) -> Passage | None:
        return self.db.query(Passage).order_by(func.random()).first()

    def get_random_passage_with_questions(self, min_questions: int = 5) -> Passage | None:
        """Get a random passage that has at least min_questions associated questions."""
        return (
            self.db.query(Passage)
            .join(ComprehensionQuestion, Passage.id == ComprehensionQuestion.passage_id)
            .group_by(Passage.id)
            .having(func.count(ComprehensionQuestion.id) >= min_questions)
            .order_by(func.random())
            .first()
        )

    def get_eligible_passages(self, limit: int = 10) -> list[Passage]:
        """Get passages that have associated questions, suitable for the reading pool."""
        return (
            self.db.query(Passage)
            .join(ComprehensionQuestion, Passage.id == ComprehensionQuestion.passage_id)
            .group_by(Passage.id)
            .having(func.count(ComprehensionQuestion.id) >= 5)
            .order_by(func.random())
            .limit(limit)
            .all()
        )

    def count_passages(self) -> int:
        return self.db.query(Passage).count()

    def passage_text_exists(self, text: str) -> bool:
        return self.db.query(Passage).filter(Passage.text == text).first() is not None

    def create_passage_session(self, user_id: UUID, passage_id: int) -> PassageSession:
        session = PassageSession(user_id=user_id, passage_id=passage_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_passage_session(self, session_id: int) -> PassageSession | None:
        return self.db.query(PassageSession).filter(PassageSession.id == session_id).first()

    def create_passage_question(
        self,
        passage_id: int,
        question_text: str,
        options: dict,
        correct_answer: str,
        difficulty: str,
    ) -> ComprehensionQuestion:
        question = ComprehensionQuestion(
            passage_id=passage_id,
            question=question_text,
            options=options,
            correct_answer=correct_answer,
            difficulty=difficulty,
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def get_questions_by_passage(
        self, passage_id: int, limit: int = 5
    ) -> list[ComprehensionQuestion]:
        return (
            self.db.query(ComprehensionQuestion)
            .filter(ComprehensionQuestion.passage_id == passage_id)
            .order_by(func.random())
            .limit(limit)
            .all()
        )

    def count_questions_by_passage(self, passage_id: int) -> int:
        return (
            self.db.query(ComprehensionQuestion)
            .filter(ComprehensionQuestion.passage_id == passage_id)
            .count()
        )

    def get_all_question_texts(self, passage_id: int) -> list[str]:
        results = (
            self.db.query(ComprehensionQuestion.question)
            .filter(ComprehensionQuestion.passage_id == passage_id)
            .all()
        )
        return [r[0] for r in results]

    def get_question_by_id(self, question_id: int) -> ComprehensionQuestion | None:
        return (
            self.db.query(ComprehensionQuestion)
            .filter(ComprehensionQuestion.id == question_id)
            .first()
        )

    def question_text_exists(self, question_text: str) -> bool:
        return (
            self.db.query(ComprehensionQuestion)
            .filter(ComprehensionQuestion.question == question_text)
            .first()
            is not None
        )

    def create_passage_answer(
        self, session_id: int, question_id: int, selected_answer: str, is_correct: bool
    ) -> PassageAnswer:
        answer = PassageAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def get_answers_by_session(self, session_id: int) -> list[PassageAnswer]:
        return self.db.query(PassageAnswer).filter(PassageAnswer.session_id == session_id).all()

    def count_attempted_questions(self, session_id: int, passage_id: int) -> int:
        return (
            self.db.query(PassageAnswer)
            .join(ComprehensionQuestion, ComprehensionQuestion.id == PassageAnswer.question_id)
            .filter(
                PassageAnswer.session_id == session_id,
                ComprehensionQuestion.passage_id == passage_id,
            )
            .count()
        )
