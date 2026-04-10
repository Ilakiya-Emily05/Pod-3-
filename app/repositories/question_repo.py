from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.question import Question


class QuestionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_question(self, question_data: dict) -> Question:
        question = Question(**question_data)
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def get_question_by_id(self, question_id: int) -> Question | None:
        return self.db.query(Question).filter(Question.id == question_id).first()

    def get_questions_by_topic(self, topic: str) -> list[Question]:
        return self.db.query(Question).filter(Question.topic == topic).all()

    def get_questions_by_subtopic(self, topic: str, subtopic: str) -> list[Question]:
        return (
            self.db.query(Question)
            .filter(Question.topic == topic, Question.subtopic == subtopic)
            .all()
        )

    def get_questions_by_topic_and_subtopic(self, topic: str, subtopic: str, limit):
        return (
            self.db.query(Question)
            .filter(Question.topic == topic, Question.subtopic == subtopic)
            .order_by(func.random())
            .limit(limit)
            .all()
        )

    def get_by_topic(self, topic: str, subtopic: str, limit: int):
        q = self.db.query(Question).filter(Question.topic == topic, Question.subtopic == subtopic)
        if hasattr(Question, "is_active"):
            q = q.filter(Question.is_active)
        return q.order_by(func.random()).limit(limit).all()

    def get_random_question(
        self, topic: str, subtopic: str, exclude_ids: list[int]
    ) -> Question | None:
        query = self.db.query(Question).filter(
            Question.topic == topic, Question.subtopic == subtopic
        )
        if exclude_ids:
            query = query.filter(~Question.id.in_(exclude_ids))
        return query.order_by(func.random()).first()

    def count_by_topic_subtopic(self, topic, subtopic):
        return (
            self.db.query(Question)
            .filter(Question.topic == topic, Question.subtopic == subtopic)
            .count()
        )

    def get_all_question_texts(self):
        results = self.db.query(Question.question_text).all()
        return [r[0] for r in results]

    def bulk_insert(self, topic, subtopic, questions) -> None:
        objs = []
        for q in questions:
            objs.append(
                Question(
                    topic=topic,
                    subtopic=subtopic,
                    question_text=q["question"],
                    options=q.get("options", {}),
                    correct_answer=q.get("correct_answer", "a"),
                )
            )
        self.db.add_all(objs)
        self.db.commit()
